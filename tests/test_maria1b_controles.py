"""MARIA-1b: controles antes de generar el TXT.

Lo que impide un TXT válido no deja generar (/generate_maria da 400 con la
lista de errores); lo dudoso avisa. Los mismos controles los devuelve
/api/validate/smart cuando la pantalla le manda la cabecera, así el semáforo
y la pantalla de generar los muestran antes.
"""
import asyncio
import io
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests.test_generar_maria_txt import GOLDEN_INPUTS

USUARIO = {"username": "m1b", "roles": ["operador"], "effective_owner": "m1b",
           "plan": "premium", "billing_status": "active"}
GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "maria_golden_anon.TXT")
# El CUIT anonimizado del archivo real (30999999990) es inventado y su dígito
# verificador no cierra: por la ruta se usa uno que sí, y se compara contra el
# archivo real con sólo esa línea cambiada.
CUIT_VALIDO = "30999999995"


def _esperado() -> str:
    with open(GOLDEN_PATH, "r", newline="") as f:
        return f.read().replace("NDDTIMMIOE=30999999990", f"NDDTIMMIOE={CUIT_VALIDO}")


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(USUARIO)
    from types import SimpleNamespace
    main.app.dependency_overrides[main.require_active_billing] = lambda: SimpleNamespace(organization_id=None)
    yield
    main.app.dependency_overrides.pop(main.get_current_user, None)
    main.app.dependency_overrides.pop(main.require_active_billing, None)


def _generar(**cambios):
    pedido = {**GOLDEN_INPUTS, "comprador_cuit": CUIT_VALIDO,
              "items": [dict(i) for i in GOLDEN_INPUTS["items"]]}
    items = cambios.pop("item", None)
    if items:
        pedido["items"][0].update(items)
    pedido.update(cambios)
    return TestClient(main.app).post("/generate_maria", json=pedido)


def _errores(r):
    assert r.status_code == 400, r.text[:400]
    return " | ".join(r.json()["detail"]["errors"])


def test_el_archivo_real_sale_identico_por_la_ruta():
    r = _generar()
    assert r.status_code == 200, r.text[:400]
    assert r.json()["content"] == _esperado()


def test_ncm_que_no_esta_en_el_nomenclador_avisa_pero_deja_generar():
    """El nomenclador que tenemos es el de 2018: una NCM que no está puede ser
    de la enmienda de 2022 (8517.13.00, teléfonos). Avisa; no frena."""
    r = _generar(item={"pieza": "99998888000A"})
    assert r.status_code == 200, r.text[:300]
    assert any("la NCM 99998888 no está en el nomenclador" in w for w in r.json()["warnings"]), r.json()


def test_ncm_que_perdio_el_0_inicial_propone_el_0():
    """01012100 en Excel se guarda como 1012100: la SIM queda con 10 dígitos."""
    errores = _errores(_generar(item={"pieza": "1012100000A"}))
    assert "¿Es 01012100000A?" in errores, errores


@pytest.mark.parametrize("moneda,mensaje", [
    ("", "Falta la moneda"),
    ("USD", "se escribe «DOL»"),
    ("DO", "no es un código de 3 letras"),
])
def test_moneda_que_impide_el_txt(moneda, mensaje):
    assert mensaje in _errores(_generar(moneda=moneda))


def test_moneda_rara_avisa_pero_deja_generar():
    r = _generar(moneda="CHF")
    assert r.status_code == 200, r.text[:300]
    assert any("CHF" in w for w in r.json()["warnings"]), r.json()["warnings"]


@pytest.mark.parametrize("incoterm,mensaje", [("", "Falta el incoterm"), ("FOX", "no es válido")])
def test_incoterm_que_impide_el_txt(incoterm, mensaje):
    assert mensaje in _errores(_generar(incoterm=incoterm))


def test_cuit_del_importador_vacio_no_deja_generar():
    """D20 (a): sin el CUIT del importador el TXT no sirve para presentar."""
    assert "Falta el CUIT del importador" in _errores(_generar(comprador_cuit=""))


@pytest.mark.parametrize("cuit,mensaje", [
    ("30999999991", "no es válido"),      # dígito verificador mal
    ("3099999999", "no es válido"),       # 10 dígitos
])
def test_cuit_del_importador(cuit, mensaje):
    assert mensaje in _errores(_generar(comprador_cuit=cuit))


@pytest.mark.parametrize("campo", ["flete", "seguro"])
def test_flete_o_seguro_negativo_no_deja_generar(campo):
    assert "no puede ser negativo" in _errores(_generar(**{campo: -1}))


@pytest.mark.parametrize("cambio", [
    {"item": {"cantidad": 0}}, {"item": {"cantidad": -2}},
    {"item": {"valor_unitario": 0, "valor_total": 0}},
    {"item": {"peso_kg": 0}},
])
def test_montos_vacios_negativos_o_en_0_no_dejan_generar(cambio):
    _errores(_generar(**cambio))


def test_todos_los_errores_juntos():
    errores = _errores(_generar(moneda="", comprador_cuit="30999999991", item={"pieza": "1012100000A"}))
    for parte in ("Falta la moneda", "CUIT del importador", "0 inicial"):
        assert parte in errores, errores


@pytest.mark.parametrize("campo", ["comprador_nombre", "vendedor_nombre", "comprador_domicilio",
                                   "vendedor_id", "operation_id"])
def test_un_texto_no_mete_lineas_ni_igual_en_el_txt(campo):
    """M10: un salto de línea con «CLAVE=valor» detrás inventaría una línea."""
    original = GOLDEN_INPUTS.get(campo) or "X"
    r = _generar(**{campo: original + "\r\nNDDTIMMIOE=20111111112\nX=1\u2028Y\x85Z\u2029W"})
    assert r.status_code == 200, r.text[:300]
    txt = r.json()["content"]
    lineas = txt.split("\r\n")
    assert "NDDTIMMIOE=20111111112" not in lineas
    assert not any(l.startswith("X=") for l in lineas)
    assert all("\n" not in l and "\r" not in l for l in lineas)
    assert not any(c in txt for c in "\u2028\u2029\x85"), "salto de línea Unicode en el TXT"
    # Cada línea es «CLAVE=valor» con un solo «=» (M10).
    assert all(l.count("=") <= 1 for l in lineas), [l for l in lineas if l.count("=") > 1]
    assert len(lineas) == len(_esperado().split("\r\n"))


def test_la_validacion_previa_devuelve_los_mismos_errores():
    items = [{"pieza": "99998888000A", "descripcion": "MAQUINA DEMO GRANDE", "origen": "AR",
              "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}]
    r = TestClient(main.app).post("/api/validate/smart", json={
        "items": items, "operacion": {"moneda": "", "incoterm": "FOB", "comprador_cuit": "30999999991"}})
    assert r.status_code == 200
    errores = " | ".join(r.json()["errores"])
    for parte in ("Falta la moneda", "CUIT del importador"):
        assert parte in errores, errores
    assert any("nomenclador" in a for a in r.json()["advertencias"]), r.json()
    assert "errores" in r.json()["resumen"] and "sin problemas" not in r.json()["resumen"]


def _cliente() -> str:
    from proyecto_maria.database.connection import AsyncSessionLocal
    from proyecto_maria.database.models import Client
    cid = str(uuid.uuid4())

    async def _crear():
        async with AsyncSessionLocal() as s:
            s.add(Client(id=cid, owner_username=USUARIO["username"], name="Importadora Demo",
                         cuit="30999999990"))
            await s.commit()
    asyncio.run(_crear())
    return cid


def _items_guardados(op_id: str):
    from sqlalchemy import select
    from proyecto_maria.database.connection import AsyncSessionLocal
    from proyecto_maria.database.models import OperationItem

    async def _leer():
        async with AsyncSessionLocal() as s:
            r = await s.execute(select(OperationItem).where(OperationItem.operation_id == op_id))
            return r.scalars().all()
    return asyncio.run(_leer())


def test_guardar_la_operacion_no_inventa_cantidad_peso_ni_origen():
    cid = _cliente()
    r = TestClient(main.app).post(f"/api/clientes/{cid}/operaciones", json={
        "items": [{"pieza": "84798999900H", "descripcion": "MAQUINA DEMO", "valor_unitario": 10}]})
    assert r.status_code in (200, 201), r.text[:300]
    op_id = r.json().get("id") or r.json().get("operation_id") or r.json().get("operacion", {}).get("id")
    assert op_id, r.json()
    (item,) = _items_guardados(op_id)
    assert (item.cantidad, item.peso_unitario, item.origen) == (0, 0, ""), (
        item.cantidad, item.peso_unitario, item.origen)


def _subir_libro(hojas: dict):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for nombre, filas in hojas.items():
        ws = wb.create_sheet(nombre)
        for f in filas:
            ws.append(f)
    buf = io.BytesIO()
    wb.save(buf)
    return TestClient(main.app).post("/upload_excel_v2/", files={
        "file": ("f.xlsx", buf.getvalue(),
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})


H = ["pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"]


def test_el_excel_deja_en_la_operacion_lo_que_no_se_leyo():
    r = _subir_libro({
        "Factura": [H, ["84713000", "Laptop", "CN", 10, 350, 1.5],
                    ["", "Freight", "", 1, 500, None]],
        "Hoja2": [H, ["85171300", "Telefono", "CN", 5, 100, 0.2]],
        "Vacia": [[" ", None, ""]],  # sólo espacios: no son datos
    })
    assert r.status_code == 200, r.text[:300]
    op = r.json()["operacion"]
    assert op.get("filas_excel_sin_leer") == [3], op
    assert op.get("filas_excel_sin_leer_total") == 1, op
    assert op.get("hojas_excel_sin_leer") == ["Hoja2"], op


def test_un_libro_de_una_hoja_no_avisa_hojas():
    r = _subir_libro({"Factura": [H, ["84713000", "Laptop", "CN", 10, 350, 1.5]]})
    assert r.status_code == 200, r.text[:300]
    assert "hojas_excel_sin_leer" not in r.json()["operacion"]


@pytest.mark.parametrize("incoterm", ["FAS", "DAT", "DDU"])
def test_incoterms_que_la_pantalla_ofrece_o_el_generador_reconoce_dejan_generar(incoterm):
    """FAS está en la lista de la revisión; DAT y DDU los reconoce el generador."""
    r = _generar(incoterm=incoterm)
    assert r.status_code == 200, r.text[:300]


def test_si_mirar_las_otras_hojas_falla_la_subida_sigue(monkeypatch):
    """Es sólo un aviso: no tira abajo una subida que se lee bien."""
    def _falla(*a):
        raise RuntimeError("libro raro")
    monkeypatch.setattr(main, "_otras_hojas_con_datos", _falla)
    r = _subir_libro({"Factura": [H, ["84713000", "Laptop", "CN", 10, 350, 1.5]],
                      "Hoja2": [H, ["85171300", "Telefono", "CN", 5, 100, 0.2]]})
    assert r.status_code == 200, r.text[:300]
    assert len(r.json()["items"]) == 1


@pytest.mark.parametrize("sufijo", ["AA(X)-AB(MOD=1)-", "AA(X)-AB(Y\x7f)-"])
def test_sufijo_sbt_con_igual_o_control_no_deja_generar(sufijo):
    r = _generar(sbt_sufijo_valor=sufijo)
    assert r.status_code == 400, r.text[:300]
    assert "sufijo" in str(r.json()["detail"]).lower(), r.json()


def test_sin_moneda_ni_incoterm_el_servidor_no_inventa_dol_ni_fob():
    pedido = {**GOLDEN_INPUTS, "comprador_cuit": CUIT_VALIDO}
    pedido.pop("moneda"); pedido.pop("incoterm")
    r = TestClient(main.app).post("/generate_maria", json=pedido)
    errores = _errores(r)
    assert "Falta la moneda" in errores and "Falta el incoterm" in errores, errores


def test_el_txt_lleva_lo_que_se_controla_normalizado():
    r = _generar(moneda=" dol ", incoterm=" ddp ", comprador_cuit="30-99999999-5")
    assert r.status_code == 200, r.text[:300]
    assert r.json()["content"] == _esperado()


def test_los_controles_con_miles_de_items_no_traban():
    import time
    from proyecto_maria.core.controles_maria import controles_antes_de_generar
    items = [{"pieza": "84798999900H"}] * 5000
    controles_antes_de_generar(items[:1], {})  # carga el catálogo
    t0 = time.monotonic()
    controles_antes_de_generar(items, {"moneda": "DOL", "incoterm": "FOB", "comprador_cuit": CUIT_VALIDO})
    assert time.monotonic() - t0 < 0.5
