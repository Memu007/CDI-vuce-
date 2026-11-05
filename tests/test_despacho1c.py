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
@pytest.mark.parametrize("guardado", [True, False, None], ids=["guardado", "no-guardado", "sin-dato"])
def test_lo_que_no_quedo_en_la_memoria_se_avisa(escenario, guardado):
    salida = subprocess.run(["node", str(PANTALLA), escenario, json.dumps(guardado)],
                            capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, salida.stderr[-800:]
    vista = json.loads(salida.stdout)
    toasts = vista["toasts"]
    if escenario == "listo-con-cliente":
        # la caja «Cliente guardado» es de la operación anterior
        assert vista["caja"] is None, vista

    avisos = [t for t in toasts if t["tipo"] == "warning"]
    if guardado is not False:
        assert avisos == [], toasts
        if escenario == "asignar-cliente":
            assert toasts and toasts[-1]["titulo"] == "Cliente guardado", toasts
    else:
        # toast reemplaza al anterior: el aviso tiene que ser lo último a la vista
        assert toasts and toasts[-1]["tipo"] == "warning" and "memoria" in toasts[-1]["titulo"], toasts


FALLAS = {"500": {"status": 500}, "409": {"status": 409}, "402": 402, "red": "red", "no-guardado": False}
FALLAS_MEMORIA = {"400": {"status": 400}, "no-guardado": False}
CON_PANEL = ("asignar-cliente", "crear-reintento")


@pytest.mark.parametrize("escenario, falla", [
    *[(e, f) for e in (*CON_PANEL, "listo-con-cliente", "listo-con-vendedor") for f in FALLAS],
    ("aprender", "400"),
    *[("confirmar-ncm", f) for f in FALLAS_MEMORIA],
])
def test_ninguna_falla_deja_un_exito_a_la_vista(escenario, falla):
    respuesta = {**FALLAS, **FALLAS_MEMORIA}[falla]
    salida = subprocess.run(["node", str(PANTALLA), escenario, json.dumps(respuesta)],
                            capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, salida.stderr[-800:]
    vista = json.loads(salida.stdout)
    toasts, caja = vista["toasts"], vista["caja"]

    # reintentar después de crear el cliente no lo crea otra vez
    assert vista["clientesCreados"] == (escenario == "crear-reintento"), vista
    # toast reemplaza al anterior: lo último que queda es lo que se ve
    tipo = "warning" if falla in ("no-guardado", "400") else "error"
    assert toasts and toasts[-1]["tipo"] == tipo, vista
    if tipo == "warning":
        assert caja is None or "memoria" in caja["texto"], vista
    else:
        assert caja is None, vista
        # el panel sigue abierto para reintentar
        assert vista["panelAbierto"] == (escenario in CON_PANEL), vista


@pytest.mark.parametrize("cambio", [None, {"id": 9, "nombre": "Otro Cliente Sintético"}], ids=["sale", "otro-cliente"])
def test_se_guarda_la_operacion_que_se_genero(cambio):
    salida = subprocess.run(["node", str(PANTALLA), "listo-y-cambia", json.dumps(cambio)],
                            capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, salida.stderr[-800:]
    # cambiar de cliente o de operación mientras aprende no cambia lo que se guarda
    assert json.loads(salida.stdout)["operaciones"] == [
        {"url": "/api/clientes/7/operaciones", "factura": "FA-1"}], salida.stdout
