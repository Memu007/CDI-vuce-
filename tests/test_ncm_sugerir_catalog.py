"""Contrato del asistente NCM: memoria confirmada > código exacto > IA validada.

El buscador lexical de ARCA (search_term) ya NO se usa como clasificador
comercial: el nomenclador acumula contexto legal de capítulos/partidas y
compartir una palabra no significa pertenecer al producto correcto. Sin
memoria confirmada ni código exacto, sólo Gemini (validado contra ARCA)
puede proponer candidatos; si no hay Gemini disponible, se devuelve [].
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from proyecto_maria import main
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Client


@pytest.mark.parametrize(
    "query",
    [
        "notebook",
        "mesa de madera",
        "motor eléctrico",
        "remera de algodón",
        "tornillo de acero",
        "TABLE",
        "botella de acero inoxidable",
    ],
)
def test_sugerir_sin_memoria_ni_gemini_no_usa_arca_lexical(
    client, auth_override, monkeypatch, query
):
    """Sin historial, sin código exacto y sin Gemini: cero resultados y mensaje claro."""
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "false")

    response = client.post("/api/ncm/sugerir", json={"descripcion": query})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["sugerencias"] == []
    assert data["message"] == "Sin coincidencia segura. Agregá material, uso o tipo de producto."


def test_sugerir_usa_gemini_validado_contra_arca_cuando_no_hay_memoria(
    client, auth_override, monkeypatch
):
    """Gemini propone candidatos; sólo se devuelven los que existen en ARCA."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-test")
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "true")
    monkeypatch.setattr(
        main,
        "_suggest_ncm_with_gemini",
        lambda descripcion, limit=5: [
            {"ncm": "84713011", "desc": "Notebook", "source": "ia", "updated_at": "2026-07-12"},
        ],
    )

    response = client.post("/api/ncm/sugerir", json={"descripcion": "notebook gamer"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["sugerencias"]) == 1
    assert data["sugerencias"][0]["ncm"] == "84713011"
    assert data["sugerencias"][0]["source"] == "ia"


def test_validate_ia_ncm_candidates_descarta_codigos_inexistentes():
    """Un código inventado por la IA nunca llega al usuario."""
    candidates = [
        {"ncm": "99999999", "desc": "código inexistente"},
        {"ncm": "84713011", "desc": "notebook"},
    ]

    validated = main._validate_ia_ncm_candidates(candidates, limit=5)

    assert len(validated) == 1
    assert validated[0]["ncm"] == "84713011"
    assert validated[0]["source"] == "ia"


@pytest.mark.parametrize("query,expected", [
    ("TABLE", False),
    ("84713011", True),
    ("8471.30.11", True),
    ("8471 30 11", True),
    ("mesa de madera", False),
])
def test_looks_like_ncm_code_query(query, expected):
    assert main._looks_like_ncm_code_query(query) is expected


@pytest.mark.parametrize("query", ["8471.30.11", "84713011", "8471 30 11"])
def test_sugerir_ncm_exacta_es_estable_ante_puntuacion(client, auth_override, query):
    response = client.post("/api/ncm/sugerir", json={"descripcion": query})

    assert response.status_code == 200, response.text
    results = response.json()["sugerencias"]
    assert len(results) == 1
    assert results[0]["ncm"] == "84713011"
    assert results[0]["source"] == "arca"


def test_sugerir_ignora_mayusculas_tildes_y_plural(client, auth_override):
    baseline = client.post("/api/ncm/sugerir", json={"descripcion": "tornillo de acero"}).json()
    variant = client.post("/api/ncm/sugerir", json={"descripcion": "TORNILLOS DE ACÉRO"}).json()

    assert [item["ncm"] for item in baseline["sugerencias"]] == [
        item["ncm"] for item in variant["sugerencias"]
    ]


def test_confirmacion_alimenta_memoria_de_cliente_y_proveedor(
    client, auth_override, monkeypatch, tmp_path
):
    """Una SIM confirmada se memoriza como NCM base, nunca como DC automático."""
    client_id = str(uuid.uuid4())
    monkeypatch.setattr(main, "_ncm_historial_path", lambda _owner: str(tmp_path / "historial.json"))

    async def seed_client():
        async with AsyncSessionLocal() as session:
            session.add(Client(id=client_id, owner_username="test_user", name="Cliente NCM"))
            await session.commit()

    asyncio.run(seed_client())
    description = "Notebook industrial de prueba"
    saved = client.post("/api/ncm/guardar-uso", json={
        "descripcion": description,
        "ncm": "8471.30.11.000A",
        "origen": "310",
        "client_id": client_id,
        "vendor_name": "Proveedor de prueba",
    })
    assert saved.status_code == 200, saved.text
    assert saved.json()["success"] is True

    by_client = client.post("/api/ncm/sugerir", json={
        "descripcion": description,
        "client_id": client_id,
    }).json()["sugerencias"]
    by_vendor = client.post("/api/ncm/sugerir", json={
        "descripcion": description,
        "vendor_name": "Proveedor de prueba",
    }).json()["sugerencias"]

    assert by_client[0] == {
        "ncm": "84713011",
        "desc": description,
        "source": "historial",
        "count": 1,
        "scope": "cliente",
    }
    assert by_vendor[0] == {
        "ncm": "84713011",
        "desc": description,
        "source": "proveedor",
        "scope": "proveedor",
    }
