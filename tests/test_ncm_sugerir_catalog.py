"""Contrato del asistente NCM local: catálogo ARCA antes que IA."""

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
    ],
)
def test_sugerir_usa_catalogo_arca_local_para_busquedas_comerciales(
    client, auth_override, monkeypatch, query
):
    """No requiere Gemini, internet ni historial para tener candidatos."""
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "false")

    response = client.post("/api/ncm/sugerir", json={"descripcion": query})

    assert response.status_code == 200, response.text
    data = response.json()
    assert 1 <= len(data["sugerencias"]) <= 5
    assert all(item["source"] == "arca" for item in data["sugerencias"])
    assert data["catalogo"]["source"] == "ARCA"
    assert data["catalogo"]["updated_at"] == "2026-07-12"


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
