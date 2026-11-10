"""DESPACHO-1c: lo que no quedó en la memoria de productos se avisa, y una
descripción que normalizada queda vacía no cruza el historial."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from proyecto_maria import main
from proyecto_maria.core import catalog_service

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


def pantalla(escenario, respuesta, opciones=None):
    args = ["node", str(PANTALLA), escenario, json.dumps(respuesta)]
    salida = subprocess.run([*args, json.dumps(opciones or {})], capture_output=True, text=True, timeout=60)
    assert salida.returncode == 0, salida.stderr[-800:]
    return json.loads(salida.stdout)


@pytest.mark.parametrize("escenario", ["listo-con-cliente", "asignar-cliente", "confirmar-ncm", "asignar-ncm"])
@pytest.mark.parametrize("guardado", [True, False, None], ids=["guardado", "no-guardado", "sin-dato"])
def test_lo_que_no_quedo_en_la_memoria_se_avisa(escenario, guardado):
    vista = pantalla(escenario, guardado)
    toasts = vista["toasts"]
    if escenario == "asignar-ncm":
        assert ("autocatalogo" in vista["hints"]) == (guardado is not False), vista
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
FALLAS_MEMORIA = {"400": {"status": 400}, "402": 402, "red": "red", "no-guardado": False,
                  "rechazado": {"success": False}}
CON_PANEL = ("asignar-cliente", "crear-reintento")


@pytest.mark.parametrize("escenario, falla", [
    *[(e, f) for e in (*CON_PANEL, "listo-con-cliente", "listo-con-vendedor") for f in FALLAS],
    *[("aprender", f) for f in ("400", "402", "red")],
    *[(e, f) for e in ("confirmar-ncm", "asignar-ncm") for f in FALLAS_MEMORIA],
])
def test_ninguna_falla_deja_un_exito_a_la_vista(escenario, falla):
    vista = pantalla(escenario, {**FALLAS, **FALLAS_MEMORIA}[falla])
    toasts, caja = vista["toasts"], vista["caja"]
    assert "autocatalogo" not in vista["hints"], vista

    # reintentar después de crear el cliente no lo crea otra vez
    assert vista["clientesCreados"] == (escenario == "crear-reintento"), vista
    # toast reemplaza al anterior: lo último que queda es lo que se ve
    solo_memoria = escenario in ("aprender", "confirmar-ncm", "asignar-ncm")
    tipo = "warning" if falla == "no-guardado" or solo_memoria else "error"
    assert toasts and toasts[-1]["tipo"] == tipo, vista
    if tipo == "warning":
        assert caja is None or "memoria" in caja["texto"], vista
    else:
        assert caja is None, vista
        # el panel sigue abierto para reintentar
        assert vista["panelAbierto"] == (escenario in CON_PANEL), vista


@pytest.mark.parametrize("cambio", [None, {"id": 9, "nombre": "Otro Cliente Sintético"}], ids=["sale", "otro-cliente"])
def test_se_guarda_la_operacion_que_se_genero(cambio):
    vista = pantalla("listo-y-cambia", cambio)
    # cambiar de cliente o de operación mientras aprende no cambia lo que se guarda
    assert vista["operaciones"] == [{"url": "/api/clientes/7/operaciones", "factura": "FA-1"}], vista


CATALOGO = {"colgado": "colgado", "400": {"status": 400}, "402": 402, "red": "red"}


@pytest.mark.parametrize("operacion", ["guardado", *FALLAS])
@pytest.mark.parametrize("catalogo", CATALOGO)
def test_la_operacion_no_espera_al_catalogo(catalogo, operacion):
    respuesta = True if operacion == "guardado" else FALLAS[operacion]
    vista = pantalla("listo-con-vendedor", respuesta, {"catalogo": CATALOGO[catalogo]})
    toasts = vista["toasts"]

    assert len(vista["operaciones"]) == 1, vista
    if operacion == "guardado":
        aviso = [] if catalogo == "colgado" else ["Algunos productos no quedaron en la memoria"]
        assert [t["titulo"] for t in toasts][-1:] == aviso, vista
    else:
        # toast reemplaza al anterior: lo último a la vista es lo que pasó con la operación
        ultimo = toasts[-1] if toasts else {}
        de_la_operacion = ultimo.get("titulo") == "No se guardó al cliente" or (
            ultimo.get("detalle") or "").startswith("La operación se guardó")
        assert de_la_operacion, vista


def test_el_aviso_del_catalogo_nombra_el_producto_que_no_se_aprendio():
    detalle = "Producto 2 («TORNILLO»): la descripción está vacía."
    vista = pantalla("listo-con-vendedor", True, {"catalogo": {"status": 400, "detail": detalle}})
    assert vista["toasts"][-1]["detalle"].startswith(detalle), vista


def test_los_productos_sin_origen_se_avisan():
    aviso = "Producto 2 («TUERCA»): No reconozco el origen «XYZ»: usá el nombre o el código del país."
    vista = pantalla("listo-con-vendedor", True, {"catalogo": {"success": True, "avisos": [aviso]}})
    assert vista["toasts"][-1] == {"titulo": "Origen no reconocido", "detalle": aviso + " Se guardaron sin origen.",
                                   "tipo": "warning"}, vista


def test_si_la_operacion_no_se_arma_se_avisa():
    vista = pantalla("listo-no-arma", True)
    assert vista["toasts"] and vista["toasts"][-1]["tipo"] == "error", vista


@pytest.mark.parametrize("vendedor", ["Ñandú " * 20, "a" * 61, "x" * 59 + " y", "Proveedor Sintético"],
                         ids=["acentos-largo", "61", "corte-en-espacio", "comun"])
def test_el_proveedor_cumple_la_regla_del_servidor(vendedor):
    vista = pantalla("aprender", True, {"vendedor": vendedor})
    [url] = vista["catalogo"]
    vendor_id = url.removeprefix("/api/catalog/").removesuffix("/productos")
    assert catalog_service.is_valid_vendor_id(vendor_id), url


@pytest.mark.parametrize("escenario, respuesta, creados", [
    # crear A y asignar B fallan: volver a crear sigue siendo A
    ("crear-asignar-crear", {"status": 500}, 1),
    # la operación siguiente, otra vez sin cliente, no reusa el creado para la anterior
    ("crear-y-otra", True, 2),
])
def test_cada_cliente_nuevo_se_crea_una_vez(escenario, respuesta, creados):
    vista = pantalla(escenario, respuesta)
    assert vista["clientesCreados"] == creados, vista
    if escenario == "crear-asignar-crear":
        assert [o["url"] for o in vista["operaciones"]] == [
            "/api/clientes/8/operaciones", "/api/clientes/7/operaciones", "/api/clientes/8/operaciones"], vista
