"""EXCEL-1: un Excel con los datos de los dos archivos reales da el mismo TXT
que la carga por PDF con esos datos.

Los dos archivos reales anonimizados son tests/fixtures/maria_golden_anon.TXT
y maria_golden_subitems_anon.TXT. Por cada uno, la misma factura entra dos
veces: como planilla por /upload_excel_v2/ y como PDF por el lector con un
Gemini falso (el de las pruebas de MARIA-1a). En los dos caminos se completa
la NCM como en el paso de NCM, se arma el pedido como la pantalla
(finalize.js, buildMariaRequest) y se genera el TXT. Tienen que ser iguales.
"""
import io

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.core.maria_generator import generate_maria_txt
from tests.test_maria1a_lectura_factura import _leer

USUARIO = {"username": "exc1t", "roles": ["operador"], "effective_owner": "exc1t",
           "plan": "premium", "billing_status": "active"}

# Lo que dice cada factura (tests/test_generar_maria_txt.py, GOLDEN_INPUTS, y
# tests/test_maria_subitems.py, ITEM_BASE), escrito como lo escribiría el
# proveedor: el país por nombre.
FACTURAS = {
    "maria_golden_anon": dict(
        ncm="84798999900H",
        items=[dict(descripcion="MAQUINA DEMO", cantidad=1, precio=5000, peso=1220, pais="Argentina")],
        cabecera=dict(operation_id="000999001", moneda="DOL", incoterm="DDP",
                      cuit_agr="20111111112", vendedor_nombre="(00999) PROVEEDOR DEMO S.A.",
                      vendedor_id="20999999991", comprador_nombre="IMPORTADORA DEMO S.A",
                      comprador_cuit="30999999990", comprador_domicilio="CALLE FALSA 123",
                      comprador_fecha_inic_activ="01/01/2010", flete=3221.66, seguro=50,
                      fecha_embarque="02/01/2026", fecha_emision="18/07/2025",
                      sbt_sufijo_valor="AA(DEMO)-AB(DEMO)-CA00-",
                      aduana_codigo="001", tipo_destinacion="IC04"),
    ),
    "maria_golden_subitems_anon": dict(
        ncm="84714900100D",
        items=[dict(descripcion="Equipo de demostracion para prueba", cantidad=6,
                    precio=1197.00, peso=33.0, pais="China")],
        cabecera=dict(operation_id="002720126", moneda="DOL", incoterm="EXW",
                      flete=365.00, seguro=75.47, fecha_emision="22/06/2026",
                      aduana_codigo="073", sbt_sufijo_valor="AA(DEMO)-CA00-"),
    ),
}


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(USUARIO)
    yield
    main.app.dependency_overrides.pop(main.get_current_user, None)


def _por_excel(factura) -> list:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["NCM", "Descripcion", "Pais de origen", "Cantidad", "Precio Unitario", "Peso Neto"])
    for it in factura["items"]:
        ws.append([factura["ncm"], it["descripcion"], it["pais"], it["cantidad"], it["precio"], it["peso"]])
    buf = io.BytesIO()
    wb.save(buf)
    r = TestClient(main.app).post(
        "/upload_excel_v2/",
        files={"file": ("factura.xlsx", buf.getvalue(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text[:300]
    return r.json()["items"]


def _por_pdf(monkeypatch, factura) -> list:
    respuesta = {
        "operacion": {},
        "items": [dict(descripcion=it["descripcion"], cantidad=it["cantidad"],
                       valor_unitario=it["precio"], peso_kg=it["peso"], origen=it["pais"])
                  for it in factura["items"]],
    }
    return _leer(monkeypatch, "pdf_directo", respuesta)["items"]


def _como_la_pantalla(items, ncm) -> list:
    """buildMariaRequest de finalize.js, después del paso de NCM."""
    return [dict(pieza=ncm, descripcion=str(it.get("descripcion") or "").strip(),
                 origen=(str(it.get("origen") or "").strip().upper() or "XX"),
                 cantidad=float(it["cantidad"]), valor_unitario=float(it["valor_unitario"]),
                 peso_unitario=float(it["peso_unitario"]),
                 codigo_parte=str(it.get("codigo_parte") or "").strip())
            for it in items]


@pytest.mark.parametrize("nombre", sorted(FACTURAS))
def test_excel_y_pdf_dan_el_mismo_txt(monkeypatch, nombre):
    factura = FACTURAS[nombre]
    excel = _como_la_pantalla(_por_excel(factura), factura["ncm"])
    pdf = _como_la_pantalla(_por_pdf(monkeypatch, factura), factura["ncm"])
    assert excel == pdf, (excel, pdf)
    txt_excel = generate_maria_txt(items=excel, **factura["cabecera"])
    txt_pdf = generate_maria_txt(items=pdf, **factura["cabecera"])
    assert txt_excel == txt_pdf
    # Y los números de la factura llegan al TXT tal cual.
    fob = sum(it["cantidad"] * it["precio"] for it in factura["items"])
    assert f"MDDTFOB={fob:.2f}" in txt_excel, txt_excel[:400]
