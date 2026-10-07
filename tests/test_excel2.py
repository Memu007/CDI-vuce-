"""EXCEL-2 (2026-10-07): lo que el Excel todavía no leía, el CSV del historial
de NCM, el aviso de mapeo, abrir un libro armado (D26 a) y, de paso, montos
que no son números y los otros CUIT.
"""
import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests.test_maria1b_controles import _entorno, _errores, _generar  # noqa: F401
from tests.test_maria1b_devolucion import EXPORT


# ------------------------------------------- de paso: montos que no son números

ENORME = 10 ** 400  # un entero JSON: float() da OverflowError


@pytest.mark.parametrize("item, mensaje", [
    ({"cantidad": ENORME}, "Cantidad inválida"),
    ({"valor_unitario": ENORME}, "Valor inválido"),
    ({"peso_kg": ENORME}, "Peso inválido"),
    ({"cantidad": [1]}, "Cantidad inválida"),
    ({"valor_unitario": {"x": 1}}, "Valor inválido"),
])
def test_un_monto_que_no_es_un_numero_da_400(item, mensaje):
    assert mensaje in _errores(_generar(item=item))


@pytest.mark.parametrize("sub", [{"cantidad": ENORME}, {"valor_unitario": [5000]}])
def test_un_monto_de_subitem_que_no_es_un_numero_da_400(sub):
    subitems = [{"cantidad": 1, "valor_unitario": 5000, "sufijo": "AA(DEMO)-CA00-", **sub}]
    assert "sub-ítem 1" in _errores(_generar(item={"subitems": subitems}))


@pytest.mark.parametrize("cambio", [{"cantidad": ENORME}, {"valor_unitario": [1]}])
def test_la_exportacion_con_un_monto_que_no_es_un_numero_da_400(cambio):
    pedido = {**EXPORT, "items": [{**EXPORT["items"][0], **cambio}]}
    r = TestClient(main.app).post("/generate_maria_export", json=pedido)
    assert r.status_code == 400, r.text[:300]


# ------------------------------------------- de paso: los otros CUIT, sólo 0-9

@pytest.mark.parametrize("campo, valor", [
    ("cuit_agr", "２０１１１１１１１１２"),
    ("cuit_agr", "20111111١١2"),
    ("vendedor_id", "２０９９９９９９９９１"),
])
def test_cuit_del_despachante_o_id_del_vendedor_con_digitos_raros_no_deja_generar(campo, valor):
    errores = _errores(_generar(**{campo: valor}))
    assert "0-9" in errores, errores


def test_un_id_del_vendedor_extranjero_con_letras_sigue_pasando():
    r = _generar(vendedor_id="91320000MA1K3F2X5P")
    assert r.status_code == 200, r.text[:300]


# ------------------------------------------- D26 (a): abrir un libro armado

import io  # noqa: E402
import time  # noqa: E402
import zipfile  # noqa: E402

from tests.test_maria1b_devolucion import FILAS, _libro_armado, _libro_normal  # noqa: E402


def _libro_con(textos_compartidos: int = 0, filas_primera: int = 0) -> bytes:
    """Un .xlsx a mano: `textos_compartidos` entradas vacías en
    sharedStrings.xml y una primera hoja con `filas_primera` filas de 60
    celdas (sin <dimension>), como los de la reproducción de la PM."""
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8"?><workbook {ns} {rel}>'
                   '<sheets><sheet name="Hoja1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
                   '</Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<?xml version="1.0" encoding="UTF-8"?><sst {ns}>'
                   + "<si/>" * textos_compartidos + '<si><t>NCM</t></si></sst>')
        celdas = "".join(f'<c r="{chr(65 + c // 26) if c >= 26 else ""}{chr(65 + c % 26)}{{f}}"><v>1</v></c>'
                         for c in range(60))
        filas = "".join(f'<row r="{f}">' + celdas.replace("{f}", str(f)) + "</row>"
                        for f in range(2, filas_primera + 2))
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0" encoding="UTF-8"?><worksheet {ns}>'
                   f'<sheetData><row r="1"><c r="A1" t="s"><v>{textos_compartidos}</v></c></row>{filas}'
                   '</sheetData></worksheet>')
    return buf.getvalue()


def _subir(contenido: bytes):
    return TestClient(main.app).post("/upload_excel_v2/", files={"file": ("factura.xlsx", contenido)})


def test_validar_un_xlsx_no_lo_abre_con_openpyxl(monkeypatch):
    """Contar las hojas desde xl/workbook.xml: openpyxl recorría cada hoja
    sin <dimension> y cargaba todos los textos compartidos sólo para contar."""
    import openpyxl
    from proyecto_maria.security import file_security

    def _no(*a, **k):
        raise AssertionError("validar abrió el libro con openpyxl")
    monkeypatch.setattr(openpyxl, "load_workbook", _no)
    assert file_security._abrir_excel(_libro_normal({"A": FILAS, "B": [["x"]]}), ".xlsx") == 2


def test_textos_compartidos_enormes_se_rechazan_antes_de_abrir(monkeypatch):
    """Como el de la reproducción: millones de textos vacíos que pesan poco
    comprimidos y, al abrir, horas de CPU y gigas de memoria."""
    import openpyxl

    def _no(*a, **k):
        raise AssertionError("se abrió el libro")
    monkeypatch.setattr(openpyxl, "load_workbook", _no)
    t0 = time.monotonic()
    r = _subir(_libro_con(textos_compartidos=3_000_000))
    assert r.status_code == 400, r.text[:300]
    assert "textos" in r.json()["detail"], r.json()
    assert time.monotonic() - t0 < 5


def test_una_primera_hoja_enorme_se_rechaza_antes_de_abrir(monkeypatch):
    monkeypatch.setenv("EXCEL_MAX_PRIMERA_HOJA_MB", "2")
    r = _subir(_libro_con(filas_primera=1500))
    assert r.status_code == 400, r.text[:300]
    assert "primera hoja" in r.json()["detail"], r.json()


def test_un_libro_normal_sigue_entrando():
    r = _subir(_libro_normal({"Factura": FILAS, "Notas": [["x"]]}))
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items_count"] == 1


def test_ocho_libros_armados_sin_medida_no_dejan_sin_lectura_a_una_subida_normal():
    """El criterio de D26 (a): 8 libros armados sin <dimension> delante y la
    subida normal da 200. Antes daba 400 a los 30 s (la validación abría cada
    libro con openpyxl, que recorría todas sus hojas para medirlas)."""
    import asyncio
    import httpx

    armado = _libro_armado(declarar_medida=False)
    normal = _libro_normal({"Factura": FILAS})

    async def _todo():
        transporte = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test", timeout=600) as c:
            def subir(contenido):
                return c.post("/upload_excel_v2/", files={"file": ("factura.xlsx", contenido)})
            pesadas = [asyncio.create_task(subir(armado)) for _ in range(8)]
            await asyncio.sleep(0.5)
            t0 = time.monotonic()
            r = await subir(normal)
            dt = time.monotonic() - t0
            otras = await asyncio.gather(*pesadas)
            return r, dt, otras

    r, dt, otras = asyncio.run(_todo())
    print(f"subida normal: {r.status_code} en {dt:.1f} s; armados: {[o.status_code for o in otras]}")
    assert r.status_code == 200, f"la subida normal dio {r.status_code} a los {dt:.1f} s: {r.text[:200]}"


def test_leer_solo_la_primera_hoja_da_lo_mismo_que_el_libro_entero(tmp_path):
    """La copia con sólo la primera hoja se lee igual que el libro entero:
    fechas, números con formato, celdas combinadas, nombres definidos y una
    hoja de gráfico antes."""
    import datetime
    import openpyxl
    import pandas as pd
    from openpyxl.chart import BarChart, Reference
    from openpyxl.workbook.defined_name import DefinedName

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Factura"
    ws.append(["NCM", "Descripcion", "Fecha", "Cantidad", "Precio Unitario"])
    ws.append(["84798999900H", "MAQUINA DEMO", datetime.date(2025, 7, 18), 1, 5000.5])
    ws.append(["84714900100D", "EQUIPO", datetime.date(2026, 6, 22), 6, 1197])
    ws["E3"].number_format = "#,##0.00"
    ws.merge_cells("B4:C4")
    ws["B4"] = "nota combinada"
    otra = wb.create_sheet("Otra")
    otra.append(["algo", 1])
    wb.defined_names["Rango"] = DefinedName("Rango", attr_text="Otra!$A$1:$B$1")
    grafico = BarChart()
    grafico.add_data(Reference(ws, min_col=4, min_row=1, max_row=3), titles_from_data=True)
    wb.create_chartsheet("Grafico", 0).add_chart(grafico)
    ruta = tmp_path / "libro.xlsx"
    wb.save(ruta)

    entero = pd.read_excel(ruta, engine="openpyxl", dtype=object).dropna(how="all")
    solo = main._leer_excel_ruta(str(ruta), "openpyxl")
    pd.testing.assert_frame_equal(entero, solo)
