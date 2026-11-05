"""DESPACHO-1c: lo que no quedó en la memoria de productos se avisa, y una
descripción que normalizada queda vacía no cruza el historial."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from proyecto_maria import main

MESA = {"ncm": "94036000", "count": 3}
OTRAS = {f"producto {n}": {"ncm": f"8471301{n}", "count": 1} for n in range(5)}


@pytest.mark.parametrize(
    "historial, consulta, esperadas",
    [
        # la fila guardada sin letras latinas no se sugiere para todo
        ({"日本語の製品": {"ncm": "84713012", "count": 1}}, "mesa de madera", []),
        ({"--- ...": {"ncm": "84713012", "count": 1}}, "mesa de madera", []),
        # la consulta sin letras latinas no recibe las primeras 5 del historial
        ({**OTRAS, "mesa de madera": MESA}, "日本語の製品", []),
        ({**OTRAS, "mesa de madera": MESA}, "क़क़ क़", []),
        # lo que sí coincide se sigue sugiriendo
        ({"日本語の製品": {"ncm": "84713012", "count": 1}, "Mesa de madera": MESA}, "mesa de madera", ["94036000"]),
    ],
    ids=["guardada-japones", "guardada-signos", "consulta-japones", "consulta-devanagari", "coincide"],
)
def test_lo_que_normaliza_a_vacio_no_cruza_el_historial(
    client, auth_override, monkeypatch, historial, consulta, esperadas
):
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "false")

    async def cargar(db, owner_username):
        return historial

    monkeypatch.setattr(main, "load_ncm_historial", cargar)

    r = client.post("/api/ncm/sugerir", json={"descripcion": consulta})

    assert r.status_code == 200, r.text
    del_historial = [s["ncm"] for s in r.json()["sugerencias"] if s["source"] == "historial"]
    assert del_historial == esperadas


PANTALLA = Path(__file__).with_name("despacho1c_pantalla.js")


@pytest.mark.parametrize("escenario", ["listo-con-cliente", "asignar-cliente", "confirmar-ncm"])
@pytest.mark.parametrize("guardado", [True, False], ids=["guardado", "no-guardado"])
def test_lo_que_no_quedo_en_la_memoria_se_avisa(escenario, guardado):
    salida = subprocess.run(["node", str(PANTALLA), escenario, json.dumps(guardado)],
                            capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, salida.stderr[-800:]
    toasts = json.loads(salida.stdout)["toasts"]

    avisos = [t for t in toasts if t["tipo"] == "warning"]
    if guardado:
        assert avisos == [], toasts
    else:
        # toast reemplaza al anterior: el aviso tiene que ser lo último a la vista
        assert toasts and toasts[-1]["tipo"] == "warning", toasts
