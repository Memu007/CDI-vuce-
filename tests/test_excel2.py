"""EXCEL-2 (2026-10-07): lo que el Excel todavía no leía, el CSV del historial
de NCM, el aviso de mapeo, abrir un libro armado (D26 a) y, de paso, montos
que no son números y los otros CUIT.
"""
import pandas as pd
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
import uuid  # noqa: E402
import time  # noqa: E402
import zipfile  # noqa: E402

from tests.test_maria1b_devolucion import FILAS, _libro_armado, _libro_normal  # noqa: E402


def _libro_con(textos_compartidos: int = 0, filas_primera: int = 0,
               nombre_textos: str = "xl/sharedStrings.xml") -> bytes:
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
                   f'<Override PartName="/{nombre_textos}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
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
                   f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="/{nombre_textos}"/>'
                   '</Relationships>')
        z.writestr(nombre_textos, f'<?xml version="1.0" encoding="UTF-8"?><sst {ns}>'
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
    assert file_security._abrir_excel(_libro_normal({"A": FILAS, "B": [["x"]]}), ".xlsx")[0] == 2


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


# ------------------------------------------- D18: lo que el Excel no leía

def _libro(filas: list, combinar: tuple = ()) -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    for fila in filas:
        ws.append(fila)
    for rango in combinar:
        ws.merge_cells(rango)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


ENCABEZADO = ["NCM", "Descripcion", "Pais de origen", "Cantidad", "Precio Unitario", "Peso Neto"]


def test_el_encabezado_no_tiene_que_estar_en_la_fila_1():
    """Logo o datos del vendedor arriba: antes, 400 con el archivo entero."""
    r = _subir(_libro([
        ["FACTURA COMERCIAL"],
        ["Proveedor: DEMO S.A.", None, None, "Fecha:", "18/07/2025"],
        [],
        ENCABEZADO,
        ["84798999900H", "MAQUINA DEMO", "Argentina", 1, 5000, 1220],
        ["84714900100D", None, None, None, None, None],
    ]))
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [i["descripcion"] for i in data["items"]] == ["MAQUINA DEMO"]
    assert data["items"][0]["valor_unitario"] == 5000 and data["items"][0]["origen"] == "AR"
    # La fila que no se pudo leer se nombra con su número en la planilla.
    assert data["operacion"].get("filas_excel_sin_leer") == [6], data["operacion"]


def test_sin_columna_de_origen_entra_con_el_origen_vacio_y_avisa():
    r = _subir(_libro([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario", "Peso Neto"],
        ["84798999900H", "MAQUINA DEMO", 1, 5000, 1220],
    ]))
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["items"][0]["origen"] == "" and data["items"][0]["valor_unitario"] == 5000
    assert any("origen" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_una_celda_combinada_hacia_abajo_vale_para_todas_sus_filas():
    r = _subir(_libro([
        ENCABEZADO,
        ["84798999900H", "MAQUINA DEMO", "China", 1, 5000, 1220],
        ["84714900100D", "EQUIPO DEMO", None, 6, 1197, 33],
        ["84714900100D", "OTRO EQUIPO", "Brasil", 2, 10, 1],
    ], combinar=("C2:C3",)))
    assert r.status_code == 200, r.text[:300]
    assert [i["origen"] for i in r.json()["items"]] == ["CN", "CN", "BR"]


def test_una_celda_combinada_hacia_el_costado_no_pisa_otra_columna():
    """Una descripción larga combinada sobre la columna del origen no es un
    origen: sólo se copia hacia abajo, en su propia columna."""
    r = _subir(_libro([
        ENCABEZADO,
        ["84798999900H", "MAQUINA DEMO", None, 1, 5000, 1220],
    ], combinar=("B2:C2",)))
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["origen"] == "", r.json()["items"]


# ------------------------------------------- el aviso de mapeo nombra la columna

def test_el_aviso_de_mapeo_nombra_la_columna_que_se_uso():
    # El catálogo del cliente guardó «Valor» para el precio y el archivo trae
    # «Precio Unitario»: gana la del archivo, y el aviso dice cuál se usó.
    efectivo, avisos = main._mapeo_efectivo(
        {"Valor": "valor_unitario", "Glosa": "descripcion"},
        {"Precio Unitario": "valor_unitario", "Descripcion": "descripcion"},
        ["Valor", "Precio Unitario", "Glosa", "Descripcion"],
    )
    assert efectivo["Precio Unitario"] == "valor_unitario" and efectivo["Glosa"] == "descripcion"
    texto = " | ".join(avisos)
    assert "«Precio Unitario»" in texto and "«Valor»" in texto, avisos
    assert "«Glosa»" in texto and "«Descripcion»" in texto, avisos


# ------------------------------------------- el CSV del historial de NCM

def _importar(contenido: bytes):
    return TestClient(main.app).post("/api/ncm/import-historial",
                                     files={"file": ("historial.csv", contenido, "text/csv")})


@pytest.mark.parametrize("nombre, texto, codificacion", [
    ("coma", "descripcion,ncm\nCafé {m},0901.21.00\nTé {m},0902.10.00\n", "utf-8"),
    ("punto y coma", "descripcion;ncm\nCafé tostado, molido {m};0901.21.00\nTé {m};0902.10.00\n", "utf-8"),
    ("latin-1", "descripción;ncm\nCafé {m};0901.21.00\nTé {m};0902.10.00\n", "latin-1"),
    ("BOM", "\ufeffNCM,Descripcion\n0901.21.00,Café {m}\n0902.10.00,Té {m}\n", "utf-8"),
])
def test_el_csv_del_historial_se_lee_con_coma_punto_y_coma_latin1_o_bom(nombre, texto, codificacion):
    # Productos distintos en cada caso: el historial es del mismo usuario.
    r = _importar(texto.format(m=uuid.uuid4().hex[:8]).encode(codificacion))
    assert r.status_code == 200, f"{nombre}: {r.text[:300]}"
    assert r.json()["importados"] == 2, f"{nombre}: {r.json()}"


def test_el_historial_en_excel_lee_solo_la_primera_hoja(monkeypatch):
    """Importar el historial desde un .xlsx también abre sólo la primera hoja."""
    leidos = []
    original = main._xlsx_solo_primera_hoja

    def _espia(origen):
        leidos.append(type(origen).__name__)
        return original(origen)
    monkeypatch.setattr(main, "_xlsx_solo_primera_hoja", _espia)
    marca = uuid.uuid4().hex[:8]
    contenido = _libro_normal({"Historial": [["descripcion", "ncm"], [f"Cafe {marca}", "0901.21.00"]],
                               "Otra": [["x"]]})
    r = TestClient(main.app).post("/api/ncm/import-historial", files={"file": ("historial.xlsx", contenido)})
    assert r.status_code == 200, r.text[:300]
    assert r.json()["importados"] == 1 and leidos == ["bytes"], (r.json(), leidos)


# ------------------------------------------- lo que encontró la revisión

def test_textos_compartidos_con_otro_nombre_tambien_se_rechazan(monkeypatch):
    """openpyxl encuentra las partes por [Content_Types].xml: el tope no se
    saltea renombrando sharedStrings.xml."""
    import openpyxl

    def _no(*a, **k):
        raise AssertionError("se abrió el libro")
    monkeypatch.setattr(openpyxl, "load_workbook", _no)
    r = _subir(_libro_con(textos_compartidos=3_000_000, nombre_textos="xl/strings.xml"))
    assert r.status_code == 400, r.text[:300]
    assert "textos" in r.json()["detail"], r.json()


def _con_libro_senuelo(contenido: bytes) -> bytes:
    """El libro real pasa a xl/real.xml (Content_Types y _rels/.rels apuntan
    ahí) y queda un xl/workbook.xml señuelo con una sola hoja."""
    entrada = zipfile.ZipFile(io.BytesIO(contenido))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            nombre = info.filename
            if nombre == "xl/workbook.xml":
                nombre = "xl/real.xml"
            elif nombre == "xl/_rels/workbook.xml.rels":
                nombre = "xl/_rels/real.xml.rels"
            elif nombre in ("[Content_Types].xml", "_rels/.rels"):
                datos = datos.replace(b"/xl/workbook.xml", b"/xl/real.xml").replace(
                    b'Target="xl/workbook.xml"', b'Target="xl/real.xml"')
            z.writestr(nombre, datos)
        # El señuelo: el mismo índice con una sola hoja.
        import re as _re
        senuelo = entrada.read("xl/workbook.xml").decode()
        hojas = _re.findall(r"<sheet [^>]*/>", senuelo)
        for h in hojas[1:]:
            senuelo = senuelo.replace(h, "")
        z.writestr("xl/workbook.xml", senuelo)
        z.writestr("xl/_rels/workbook.xml.rels", entrada.read("xl/_rels/workbook.xml.rels"))
    return buf.getvalue()


def test_un_libro_senuelo_no_engana_a_la_validacion_ni_a_la_lectura():
    import openpyxl
    from proyecto_maria.security import file_security

    libro = _con_libro_senuelo(_libro_normal({"Factura": FILAS, "B": [["x"]], "C": [["y"]]}))
    # openpyxl abre el libro real (3 hojas); la validación cuenta las mismas.
    assert len(openpyxl.load_workbook(io.BytesIO(libro), read_only=True).sheetnames) == 3
    assert file_security._abrir_excel(libro, ".xlsx")[0] == 3
    # La copia para leer deja una sola hoja en el libro que openpyxl abre.
    copia, _ = main._xlsx_solo_primera_hoja(libro)
    assert openpyxl.load_workbook(io.BytesIO(copia), read_only=True).sheetnames == ["Factura"]


def test_una_combinada_con_cantidad_y_precio_no_duplica_el_producto():
    """Proforma china: un producto en dos filas (la segunda sigue la
    descripción) con NCM, origen, cantidad, precio y peso combinados. El FOB
    no se duplica: los números no se copian hacia abajo."""
    r = _subir(_libro([
        ENCABEZADO,
        ["84713000", "Notebook 14 pulgadas", "China", 10, 500, 20],
        [None, "con cargador y funda", None, None, None, None],
        ["84714900100D", "Equipo", "China", 1, 120, 1],
    ], combinar=("A2:A3", "C2:C3", "D2:D3", "E2:E3", "F2:F3")))
    assert r.status_code == 200, r.text[:300]
    items = r.json()["items"]
    fob = sum(i["cantidad"] * i["valor_unitario"] for i in items)
    assert fob == 5120, items


def test_un_encabezado_en_dos_filas_combinadas_no_da_un_producto_fantasma():
    r = _subir(_libro([
        ["FACTURA"],
        [],
        ["NCM", "Descripción", "Pais de origen", "Cantidad", "Precio Unitario", "Peso Neto"],
        [None, None, None, None, "USD", "kg"],
        ["84798999900H", "MAQUINA DEMO", "Argentina", 1, 5000, 1220],
    ], combinar=("A3:A4", "B3:B4", "C3:C4", "D3:D4")))
    assert r.status_code == 200, r.text[:300]
    assert [i["descripcion"] for i in r.json()["items"]] == ["MAQUINA DEMO"], r.json()["items"]


def test_un_texto_enorme_arriba_no_traba_la_busqueda_del_encabezado():
    """Celdas de las primeras filas que apuntan a un texto enorme: la búsqueda
    del encabezado no las normaliza (con uno de casi 10 MB costaba ~2 s por
    celda; acá 1 MB, para que sin el tope falle por tiempo y no por el
    límite de la suite)."""
    enorme = "x" * 1_000_000
    filas = [[enorme] * 4 for _ in range(31)] + [ENCABEZADO, ["84798999900H", "MAQUINA", "Argentina", 1, 5, 1]]
    t0 = time.monotonic()
    import pandas as pd
    df = main._con_encabezado(pd.DataFrame(filas[1:], columns=filas[0] + [None] * 2))
    assert time.monotonic() - t0 < 3
    assert df is not None


def test_con_mapeo_del_cliente_el_pie_no_se_toma_como_encabezado():
    """El encabezado del cliente no tiene nombres conocidos («Part, Goods»)
    pero su mapeo guardado sí los reconoce: no se busca otra fila, y un pie
    con «Peso Neto | Valor» no pasa a ser el encabezado."""
    import pandas as pd
    df = pd.DataFrame(
        [["84798999900H", "MAQUINA", 1, 5000, "AR"], ["84714900100D", "EQUIPO", 2, 10, "CN"],
         ["Bultos", "Peso Neto", "Valor", None, None]],
        columns=["Part", "Goods", "Qty", "Unit USD", "Made"])
    conocidas = {"Part", "Goods", "Qty", "Unit USD", "Made"}
    assert list(main._con_encabezado(df, conocidas).columns) == list(df.columns)


@pytest.mark.parametrize("nombre, texto, crudo, esperado", [
    ("utf-8 con un byte latin-1", "descripcion,ncm\nCafé {m},0901.21.00\n", "\xe9", "Café"),
    ("BOM y un byte latin-1", "﻿descripcion,ncm\nCafé {m},0901.21.00\n", "\xe9", "Café"),
])
def test_un_csv_utf8_con_un_byte_raro_no_se_rompe_entero(nombre, texto, crudo, esperado):
    marca = uuid.uuid4().hex[:8]
    contenido = texto.format(m=marca).encode("utf-8") + f"Té {marca}x,0902.10.00\n".replace("é", crudo).encode("latin-1")
    df = main._leer_tabla(contenido, "historial.csv")
    assert list(df.columns) == ["descripcion", "ncm"], (nombre, list(df.columns))
    assert df["descripcion"][0] == f"{esperado} {marca}", (nombre, df["descripcion"][0])


def test_el_separador_no_cuenta_lo_que_va_entre_comillas():
    df = main._leer_tabla('"desc, larga";ncm\n"Cafe, molido";0901.21.00\n'.encode(), "historial.csv")
    assert list(df.columns) == ["desc, larga", "ncm"], list(df.columns)


@pytest.mark.parametrize("cuit", ["2O111111112", "abc", "20111111112​", "2011111111"])
def test_el_cuit_del_despachante_va_solo_con_11_digitos(cuit):
    assert "CUIT del despachante" in _errores(_generar(cuit_agr=cuit))


def test_el_cuit_del_despachante_con_guiones_se_normaliza():
    r = _generar(cuit_agr="20-11111111-2")
    assert r.status_code == 200, r.text[:300]
    assert "CDDTAGR=20111111112" in r.json()["content"]


@pytest.mark.parametrize("cambio", [
    {"items": [[1]]}, {"items": ["x"]}, {"items": [None]},
    {"item": {"subitems": 5}}, {"item": {"subitems": "abc"}}, {"item": {"subitems": [[1, 2]]}},
])
def test_productos_mal_formados_dan_400(cambio):
    r = _generar(**cambio)
    assert r.status_code == 400, r.text[:300]


def test_una_hoja_que_falta_en_el_archivo_da_400():
    entrada = zipfile.ZipFile(io.BytesIO(_libro_normal({"Factura": FILAS})))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for info in entrada.infolist():
            if info.filename != "xl/worksheets/sheet1.xml":
                z.writestr(info.filename, entrada.read(info.filename))
    r = _subir(buf.getvalue())
    assert r.status_code == 400, r.text[:300]
    assert "dev_detail" not in r.json()


def test_leer_la_factura_abre_un_libro_con_una_sola_hoja(monkeypatch, tmp_path):
    """Lo que recibe pandas es la copia con sólo la primera hoja: openpyxl no
    recorre las demás (las sin <dimension> costaban segundos cada una)."""
    import openpyxl
    vistos = []
    original = main.pd.read_excel

    def _espia(origen, *a, **k):
        if hasattr(origen, "getvalue"):
            vistos.append(openpyxl.load_workbook(io.BytesIO(origen.getvalue()), read_only=True).sheetnames)
        return original(origen, *a, **k)
    monkeypatch.setattr(main.pd, "read_excel", _espia)
    ruta = str(tmp_path / "tres_hojas.xlsx")
    with open(ruta, "wb") as f:
        f.write(_libro_normal({"Factura": FILAS, "B": [["x"]], "C": [["y"]]}))
    main._leer_excel_ruta(ruta, "openpyxl")
    assert vistos == [["Factura"]], vistos


# ------------------------------------------- devolución de EXCEL-2 (veredicto 2034b85)

def _con_combinadas_crudas(contenido: bytes, rangos: list) -> bytes:
    """El libro con <mergeCell> escritos a mano en la primera hoja: openpyxl
    no deja armar una combinada de un millón de filas sin crearlas."""
    import re
    import zipfile
    entrada = zipfile.ZipFile(io.BytesIO(contenido))
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                xml = re.sub(rb"<mergeCells\b.*?</mergeCells>", b"", datos.decode().encode(), flags=re.S)
                extra = ("<mergeCells count=\"%d\">" % len(rangos)
                         + "".join(f'<mergeCell ref="{r}"/>' for r in rangos) + "</mergeCells>").encode()
                datos = xml.replace(b"</sheetData>", b"</sheetData>" + extra, 1)
            z.writestr(info, datos)
    return salida.getvalue()


def test_una_combinada_gigante_repetida_no_traba_la_lectura():
    """Devolución 1: C2:C1048576 repetida 2000 veces ocupaba un hilo ~1000 s.
    El trabajo tiene que ser proporcional a las filas de la tabla."""
    import time
    contenido = _con_combinadas_crudas(_libro([
        ENCABEZADO,
        ["84798999900H", "MAQUINA DEMO", "China", 1, 5000, 1220],
        ["84714900100D", "EQUIPO DEMO", None, 6, 1197, 33],
    ]), ["C2:C1048576"] * 2000)
    import threading
    salida = {}
    hilo = threading.Thread(target=lambda: salida.update(r=_subir(contenido)), daemon=True)
    inicio = time.monotonic()
    hilo.start()
    hilo.join(10)
    tardo = time.monotonic() - inicio
    assert not hilo.is_alive(), "la lectura sigue trabada a los 10 s"
    r = salida["r"]
    assert r.status_code == 200, r.text[:300]
    assert [i["origen"] for i in r.json()["items"]] == ["CN", "CN"]
    assert tardo < 5, f"tardó {tardo:.1f} s"  # antes, ~1000 s; con margen para una máquina cargada


@pytest.mark.parametrize("cantidad, precio", [("5 UN", "USD 100"), ("5", "$ 1.500,00")])
def test_una_combinada_en_cantidad_o_precio_con_texto_no_se_copia(cantidad, precio):
    """Devolución 2: la regla es por columna; en cantidad, valor y peso no
    se copia nada, aunque el valor sea texto («5 UN», «USD 100»)."""
    r = _subir(_libro([
        ENCABEZADO,
        ["84713000", "Notebook", "China", cantidad, precio, "2 KG"],
        ["84713000", "Notebook con funda", None, None, None, None],
    ], combinar=("C2:C3", "D2:D3", "E2:E3", "F2:F3")))
    assert r.status_code == 200, r.text[:300]
    items = r.json()["items"]
    segunda = next(i for i in items if i["descripcion"] == "Notebook con funda")
    assert (segunda["cantidad"], segunda["valor_unitario"], segunda["peso_unitario"]) == (0, 0, 0), items
    assert segunda["origen"] == "CN", items


def test_una_combinada_en_la_columna_de_cantidad_del_mapeo_del_cliente_tampoco_se_copia():
    """Columnas que sólo el mapeo guardado del cliente conoce: la de cantidad
    no se rellena y la de origen sí."""
    columnas = ["Articulo X", "Bul", "Hecho en"]
    assert not main._detect_item_columns(columnas)  # sin el mapeo no se sabe qué son
    df = pd.DataFrame([["Notebook", "5 UN", "China"], ["Funda", None, None]], columns=columnas)
    salida = main._rellenar_combinadas(df.copy(), [(2, 2, 3, 2), (2, 3, 3, 3)],
                                       mapeo={"Articulo X": "descripcion", "Bul": "cantidad",
                                              "Hecho en": "origen"})
    assert pd.isna(salida.at[1, "Bul"]) and salida.at[1, "Hecho en"] == "China", salida


def test_una_fila_vacia_dentro_de_una_combinada_no_es_una_fila_sin_leer():
    """Devolución 6: rellenar antes de sacar las filas vacías la marcaba."""
    r = _subir(_libro([
        ENCABEZADO,
        ["84798999900H", "MAQUINA DEMO", "China", 1, 5000, 1220],
        [None, None, None, None, None, None],
        ["84714900100D", "EQUIPO DEMO", None, 6, 1197, 33],
    ], combinar=("C2:C4",)))
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [i["origen"] for i in data["items"]] == ["CN", "CN"]
    assert not data["operacion"].get("filas_excel_sin_leer"), data["operacion"]


@pytest.mark.parametrize("par", ["é®", "ñ\xa0", "ó¿", "Â°"])
def test_un_csv_cp1252_con_un_par_que_parece_utf8_no_pierde_las_tildes(par):
    """Devolución 5: un par cp1252 que parece UTF-8 mandaba todo el archivo
    a UTF-8 con reemplazo («Acci�n»)."""
    texto = f"descripcion;ncm\nAcción {par};0901.21.00\nBebé;0902.10.00\nNiño;0903.00.00\n"
    df = main._leer_tabla(texto.encode("cp1252"), "historial.csv")
    assert list(df["descripcion"]) == [f"Acción {par}", "Bebé", "Niño"], list(df["descripcion"])


def test_un_csv_con_codificacion_dudosa_avisa():
    """Mitad UTF-8 y mitad cp1252: se lee como se puede, pero se avisa."""
    contenido = "descripcion;ncm\nAcción;0901.21.00\n".encode("utf-8") + "Bebé;0902.10.00\n".encode("cp1252")
    df = main._leer_tabla(contenido, "historial.csv")
    assert df.attrs.get("aviso_codificacion"), df.attrs
    r = _importar(contenido.replace(b"Acci", f"Acci{uuid.uuid4().hex[:6]}".encode()))
    assert r.status_code == 200 and r.json().get("aviso"), r.json()


@pytest.mark.parametrize("item", [{"cantidad": ENORME}, {"cantidad": [1]}])
def test_una_cantidad_mala_nombra_solo_la_cantidad(item):
    """De paso (devolución de EXCEL-2): con la cantidad mala, el 400 traía
    también «Valor inválido» y «Peso inválido» con valor y peso buenos."""
    errores = _errores(_generar(item=item))
    assert "Cantidad inválida" in errores
    assert "Valor inválido" not in errores and "Peso inválido" not in errores, errores


def test_un_sub_item_con_la_cantidad_mala_nombra_solo_la_cantidad():
    from proyecto_maria.core.controles_maria import montos_fuera_de_rango
    errores = montos_fuera_de_rango([{"cantidad": 1, "valor_unitario": 1,
                                      "subitems": [{"cantidad": ENORME, "valor_unitario": 5}]}], {})
    assert errores == ["Item 1, sub-ítem 1: Cantidad inválida"], errores


def _con_estilos(contenido: bytes, elemento: str, n: int) -> bytes:
    import re
    import zipfile
    entrada = zipfile.ZipFile(io.BytesIO(contenido))
    contenedor = {"xf": "cellXfs", "font": "fonts", "dxf": "dxfs"}[elemento]
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/styles.xml":
                xml = datos.decode()
                if f"<{contenedor}" in xml:
                    xml = re.sub(rf"(<{contenedor}[^>]*?)(/>|>)",
                                 lambda m: m.group(1) + ">" + f"<{elemento}/>" * n
                                 + ("" if m.group(2) == ">" else f"</{contenedor}>"), xml, count=1)
                else:
                    xml = xml.replace("</styleSheet>", f"<{contenedor}>" + f"<{elemento}/>" * n
                                      + f"</{contenedor}></styleSheet>")
                datos = xml.encode()
            z.writestr(info, datos)
    return salida.getvalue()


@pytest.mark.parametrize("elemento", ["xf", "font", "dxf"])
def test_estilos_con_millones_de_elementos_se_rechazan_antes_de_abrir(elemento, monkeypatch):
    """Devolución 3: 10 MB de <xf/> (17 KB comprimido) pasaba la validación y
    llegaba a 1,4 GB. El tope es por elementos, no por MB: cada uno ocupa
    medio KB en memoria."""
    import openpyxl
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *a, **k: pytest.fail("abrió el libro"))
    contenido = _con_estilos(_libro([ENCABEZADO, ["84713000", "X", "China", 1, 2, 3]]), elemento,
                             (10 * 2**20 - 20_000) // (len(elemento) + 3))  # justo bajo el tope de MB
    with pytest.raises(ExcelDemasiadoGrande):
        _contar_hojas_xlsx(contenido)
    r = _subir(contenido)
    assert r.status_code == 400 and "Excel" in r.text, r.text[:300]


def test_estilos_de_un_libro_normal_grande_siguen_pasando():
    """Un libro con estilos de sobra (50.000 formatos) sigue entrando."""
    from proyecto_maria.security.file_security import _contar_hojas_xlsx
    assert _contar_hojas_xlsx(_con_estilos(_libro([ENCABEZADO]), "xf", 50_000))[0] == 1


def _con_hoja_escondida(filas: int) -> bytes:
    """Devolución 4 (a): la primera hoja chica y una segunda grande, sin
    <dimension>, con el mismo nombre y una relación de Type raro. openpyxl la
    abre igual (abre como hoja todo lo que no es de gráfico)."""
    import zipfile
    grande = zipfile.ZipFile(io.BytesIO(_libro_con(filas_primera=filas)))
    chica = zipfile.ZipFile(io.BytesIO(_libro_con(filas_primera=1)))
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in chica.infolist():
            datos = chica.read(info.filename)
            if info.filename == "xl/workbook.xml":
                datos = datos.replace(b"</sheets>", b'<sheet name="Hoja1" sheetId="2" r:id="rId9"/></sheets>')
            if info.filename == "xl/_rels/workbook.xml.rels":
                datos = datos.replace(b"</Relationships>", b'<Relationship Id="rId9" Type="http://example.com/'
                                      b'relationships/rara" Target="worksheets/sheet2.xml"/></Relationships>')
            z.writestr(info, datos)
        z.writestr("xl/worksheets/sheet2.xml", grande.read("xl/worksheets/sheet1.xml"))
    return salida.getvalue()


def test_una_hoja_con_una_relacion_rara_cuenta_y_sale_de_la_copia():
    import zipfile
    from proyecto_maria.security.file_security import hojas_del_xlsx
    contenido = _con_hoja_escondida(3)
    assert [p for _, p in hojas_del_xlsx(zipfile.ZipFile(io.BytesIO(contenido)))] == \
        ["xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"]
    copia, _ = main._xlsx_solo_primera_hoja(contenido)
    assert "xl/worksheets/sheet2.xml" not in zipfile.ZipFile(io.BytesIO(copia)).namelist()


def test_una_primera_hoja_de_27_mb_se_rechaza():
    """Devolución 4 (b): 27 MB sin <dimension> pasaban el tope de 30 MB y,
    con 8 así delante, la subida normal daba 504. El tope baja a 10 MB."""
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    with pytest.raises(ExcelDemasiadoGrande):
        _contar_hojas_xlsx(_libro_con(filas_primera=int(27 * 2**20 / 1500)))
    assert _contar_hojas_xlsx(_libro_con(filas_primera=int(9.5 * 2**20 / 1500)))[0] == 1


def test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal(monkeypatch):
    """Ocho hojas realmente bajo 10 MiB entran al validador antes de la normal."""
    import asyncio
    import httpx
    from proyecto_maria.security import file_security

    filas = 6000
    for _ in range(3):
        armado = _libro_con(filas_primera=filas)
        with zipfile.ZipFile(io.BytesIO(armado)) as z:
            tamano = z.getinfo("xl/worksheets/sheet1.xml").file_size
        if 9.5 * 2**20 < tamano < 10 * 2**20:
            break
        filas = int(filas * (9.8 * 2**20) / tamano)
    assert 9.5 * 2**20 < tamano < 10 * 2**20, (filas, tamano)
    normal = _libro_normal({"Factura": FILAS})

    async def _todo():
        entradas = 0
        listas = asyncio.Event()
        validar = file_security.validar_con_carril
        async def observar(file, *args, **kwargs):
            nonlocal entradas
            nombre = file.filename
            if nombre == "pesada.xlsx":
                entradas += 1
                if entradas == 8:
                    listas.set()
            contents, liviano = await validar(file, *args, **kwargs)
            carriles.add((nombre, liviano))
            return contents, liviano
        monkeypatch.setattr(file_security, "validar_con_carril", observar)
        transporte = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test", timeout=600) as c:
            def subir(contenido, nombre):
                return c.post("/upload_excel_v2/", files={"file": (nombre, contenido)})
            pesadas = [asyncio.create_task(subir(armado, "pesada.xlsx")) for _ in range(8)]
            await asyncio.wait_for(listas.wait(), 10)
            t0 = time.monotonic()
            r = await subir(normal, "normal.xlsx")
            dt = time.monotonic() - t0
            await asyncio.gather(*pesadas)
            assert entradas == 8
            return r, dt

    carriles = set()
    r, dt = asyncio.run(_todo())
    print(f"XML: {tamano} bytes; zip: {len(armado)} bytes; entradas: 8; normal: {r.status_code} en {dt:.1f} s")
    # El tiempo va primero: si la normal espera detrás de las pesadas, su
    # validación puede no terminar y su carril no llega a anotarse.
    assert dt < 5, f"la subida normal tardó {dt:.1f} s: esperó detrás de las pesadas"
    assert r.status_code == 200, f"la subida normal dio {r.status_code} a los {dt:.1f} s: {r.text[:200]}"
    # Las pesadas van al carril pesado y la normal al liviano (EXCEL-2b): si
    # no, el tiempo de la normal no prueba nada.
    assert carriles == {("pesada.xlsx", False), ("normal.xlsx", True)}, carriles


def test_la_pantalla_muestra_el_aviso_del_csv():
    """El aviso de codificación llegaba en el JSON y la pantalla no lo leía."""
    from pathlib import Path
    js = (Path(__file__).resolve().parents[1] / "proyecto_maria/static/v2/screens/ncm.js").read_text()
    cuerpo = js[js.index("function renderNcmImportResult"):]
    cuerpo = cuerpo[:cuerpo.index("\n    }\n")]
    assert "d.aviso" in cuerpo and "textContent = d.aviso" in cuerpo, cuerpo


def _con_celdas_en_la_ultima_columna(filas: int) -> bytes:
    """Un libro normal con `filas` filas de una celda en XFD (la columna
    16.384), sin <dimension>: pandas rellena cada fila hasta ahí."""
    import zipfile
    entrada = zipfile.ZipFile(io.BytesIO(_libro([ENCABEZADO, ["84713000", "X", "China", 1, 2, 3]])))
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                extra = "".join(f'<row r="{k}"><c r="XFD{k}"><v>1</v></c></row>' for k in range(3, filas + 3))
                datos = datos.replace(b"</sheetData>", extra.encode() + b"</sheetData>", 1)
            z.writestr(info, datos)
    return salida.getvalue()


def test_una_celda_en_la_ultima_columna_se_rechaza_antes_de_abrir(monkeypatch):
    """2.000 filas con una celda en XFD (15 KB comprimido) llegaban a 943 MB
    al leer; 8.000, a 4,2 GB (revisión de la devolución de EXCEL-2)."""
    import openpyxl
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *a, **k: pytest.fail("abrió el libro"))
    with pytest.raises(ExcelDemasiadoGrande, match="columna"):
        _contar_hojas_xlsx(_con_celdas_en_la_ultima_columna(3))


def test_una_factura_ancha_sigue_entrando():
    from proyecto_maria.security.file_security import _contar_hojas_xlsx
    assert _contar_hojas_xlsx(_libro([[f"col{c}" for c in range(200)]]))[0] == 1


# ------------------------------------------- revisión Opus de la devolución

def _cambiar_parte(contenido: bytes, parte: str, cambio) -> bytes:
    import zipfile
    entrada = zipfile.ZipFile(io.BytesIO(contenido))
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            z.writestr(info, cambio(datos) if info.filename == parte else datos)
    return salida.getvalue()


def _con_entidad(datos: bytes) -> bytes:
    """Una entidad interna que se expande a etiquetas, como el ataque."""
    raiz = datos.index(b"?>") + 2 if datos.startswith(b"<?xml") else 0
    return datos[:raiz] + b'<!DOCTYPE x [<!ENTITY a "<b/>">]>' + datos[raiz:]


@pytest.mark.parametrize("parte", ["xl/styles.xml", "xl/workbook.xml", "xl/worksheets/sheet1.xml"])
def test_un_libro_con_entidades_xml_se_rechaza_antes_de_abrir(parte, monkeypatch):
    """Revisión Opus: 5 KB con entidades se expandían a millones de <xf/> y
    llegaban a 1,9 GB; un .xlsx de verdad nunca trae DTD."""
    import openpyxl
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *a, **k: pytest.fail("abrió el libro"))
    contenido = _cambiar_parte(_libro([ENCABEZADO, ["84713000", "X", "China", 1, 2, 3]]), parte, _con_entidad)
    with pytest.raises((ExcelDemasiadoGrande, ValueError)):
        _contar_hojas_xlsx(contenido)
    assert _subir(contenido).status_code == 400


def test_estilos_con_un_prefijo_no_ascii_tambien_se_cuentan():
    """Revisión Opus: <ñ:font/> no lo contaba el patrón y 10 MB llegaban a
    948 MB."""
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    xml = (f'<?xml version="1.0" encoding="UTF-8"?><ñ:styleSheet xmlns:ñ="{ns}"><ñ:fonts>'
           + "<ñ:font/>" * 600_000 + "</ñ:fonts></ñ:styleSheet>").encode()
    contenido = _cambiar_parte(_libro([ENCABEZADO]), "xl/styles.xml", lambda _: xml)
    with pytest.raises(ExcelDemasiadoGrande):
        _contar_hojas_xlsx(contenido)


def test_estilos_de_un_libro_real_con_muchos_formatos_siguen_pasando():
    """Revisión Opus: 40.000 formatos con su alineación y 10.000 fuentes
    (220.000 etiquetas, dentro de lo que deja Excel) se rechazaban."""
    from proyecto_maria.security.file_security import _contar_hojas_xlsx
    # Las mismas 230 000 etiquetas, con no más formatos de celda de los que guarda Excel.
    libro = _con_estilos(_con_estilos(_libro([ENCABEZADO]), "xf", 40_000), "font", 190_000)
    assert _contar_hojas_xlsx(libro)[0] == 1


def _con_hoja_de_grafico(contenido: bytes, tam: int) -> bytes:
    """El libro con una hoja de gráfico de `tam` bytes y su .rels."""
    import zipfile
    entrada = zipfile.ZipFile(io.BytesIO(contenido))
    salida = io.BytesIO()
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/workbook.xml":
                datos = datos.replace(b"</sheets>", b'<sheet name="Grafico" sheetId="9" r:id="rId99"/></sheets>')
            if info.filename == "xl/_rels/workbook.xml.rels":
                datos = datos.replace(b"</Relationships>", b'<Relationship Id="rId99" Type="http://schemas.'
                                      b'openxmlformats.org/officeDocument/2006/relationships/chartsheet" '
                                      b'Target="chartsheets/sheet1.xml"/></Relationships>')
            z.writestr(info, datos)
        z.writestr("xl/chartsheets/sheet1.xml", f'<chartsheet {ns}>'.encode() + b"<a/>" * (tam // 4) + b"</chartsheet>")
        z.writestr("xl/chartsheets/_rels/sheet1.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
    return salida.getvalue()


def test_la_copia_de_la_primera_hoja_saca_las_hojas_de_grafico():
    """Revisión Opus: openpyxl lee entera una hoja de gráfico aun en
    read_only; una de 80 MB llegaba a 2,1 GB. Con una sola hoja de cálculo
    la copia devolvía el libro sin tocar."""
    import zipfile
    contenido = _con_hoja_de_grafico(_libro([ENCABEZADO, ["84713000", "X", "China", 1, 2, 3]]), 1000)
    copia, _ = main._xlsx_solo_primera_hoja(contenido)
    nombres = zipfile.ZipFile(io.BytesIO(copia)).namelist()
    assert "xl/chartsheets/sheet1.xml" not in nombres, nombres
    assert b"Grafico" not in zipfile.ZipFile(io.BytesIO(copia)).read("xl/workbook.xml")
    r = _subir(contenido)
    assert r.status_code == 200 and len(r.json()["items"]) == 1, r.text[:300]


def test_la_copia_deja_solo_la_primera_hoja_aunque_otra_se_llame_igual():
    import zipfile
    contenido = _con_hoja_escondida(3)
    copia, _ = main._xlsx_solo_primera_hoja(contenido)
    libro = zipfile.ZipFile(io.BytesIO(copia)).read("xl/workbook.xml")
    assert libro.count(b"<sheet ") == 1, libro


def test_un_rels_de_hoja_enorme_se_rechaza():
    """Revisión Opus: el .rels de la primera hoja (90 MB) se lee entero."""
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    rels = (b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + b"<x/>" * (2 * 2**20 // 4) + b"</Relationships>")
    import zipfile
    contenido = _libro([ENCABEZADO])
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in zipfile.ZipFile(io.BytesIO(contenido)).infolist():
            z.writestr(info, zipfile.ZipFile(io.BytesIO(contenido)).read(info.filename))
        z.writestr("xl/worksheets/_rels/sheet1.xml.rels", rels)
    with pytest.raises(ExcelDemasiadoGrande):
        _contar_hojas_xlsx(salida.getvalue())


def test_una_columna_detectada_como_cantidad_no_se_rellena_aunque_el_mapeo_diga_otra_cosa():
    """Revisión Opus: con «Quantity» guardada como descripción en el mapeo
    (dos columnas para descripción), «5 UN» se copiaba y el FOB se duplicaba."""
    df = pd.DataFrame([["Notebook", "5 UN", "100"], ["Funda", None, None]],
                      columns=["Producto", "Quantity", "Unit Price"])
    salida = main._rellenar_combinadas(df.copy(), [(2, 2, 3, 2)],
                                       mapeo={"Producto": "descripcion", "Quantity": "descripcion"})
    assert pd.isna(salida.at[1, "Quantity"]), salida


@pytest.mark.parametrize("texto, esperado", [
    ("descripcion;ncm\nCAFÉ\xa0TOSTADO;0901\nMANÍ\xa0PELADO;1202\nTÉ VERDE;0902\n",
     ["CAFÉ\xa0TOSTADO", "MANÍ\xa0PELADO", "TÉ VERDE"]),
    ("descripcion;ncm\n“CAFÉ”;0901\nPURÉ;2005\n", ["“CAFÉ”", "PURÉ"]),
])
def test_un_csv_cp1252_con_letras_que_arman_utf8_raro_se_lee_bien(texto, esperado):
    """Revisión Opus: «É» seguida de un espacio duro arma «ɠ» en UTF-8; eso
    no es castellano y no cuenta como UTF-8."""
    df = main._leer_tabla(texto.encode("cp1252"), "historial.csv")
    assert list(df["descripcion"]) == esperado, list(df["descripcion"])
    assert not df.attrs.get("aviso_codificacion"), df.attrs


@pytest.mark.parametrize("comilla", ['"', "'"])
@pytest.mark.parametrize("espacio", ["", " ", "\t\n"])
@pytest.mark.parametrize("referencia,admitida", [("IV1", True), ("IW1", False), ("XFD1", False), ("&#88;FD1", False)])
def test_tope_columnas_lee_atributos_xml_validos(comilla, espacio, referencia, admitida, monkeypatch):
    """Una sola celda: comillas, espacios o entidades no eluden el tope 256."""
    import re
    import zipfile
    import openpyxl
    from proyecto_maria.security.file_security import ExcelDemasiadoGrande, _contar_hojas_xlsx
    original = _libro([["sintetico"]])
    salida = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as entrada, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                datos = re.sub(rb"<dimension[^>]*/>", b"", datos)
                atributo = f"<c r{espacio}={espacio}{comilla}{referencia}{comilla}".encode()
                datos = datos.replace(b'<c r="A1"', atributo)
            z.writestr(info, datos)
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *a, **k: pytest.fail("abrió el libro"))
    if admitida:
        assert _contar_hojas_xlsx(salida.getvalue())[0] == 1
    else:
        with pytest.raises(ExcelDemasiadoGrande, match="columna"):
            _contar_hojas_xlsx(salida.getvalue())


def test_la_medida_de_la_hoja_acepta_namespace_y_atributos_con_mayor_que():
    from proyecto_maria.security.file_security import _medida_hoja
    xml = b"<s:worksheet xmlns:s='urn:test'><s:sheetData><s:row><s:c otro='a>b' r = 'IW1'/></s:row></s:sheetData></s:worksheet>"
    assert _medida_hoja(xml)[0] == 257



def test_tope_columnas_corta_y_cierra_la_fuente(monkeypatch):
    from xml.etree import ElementTree as ET
    from proyecto_maria.security.file_security import _medida_hoja
    fuentes = []
    def eventos(fuente, **kwargs):
        fuentes.append(fuente)
        yield "start", ET.Element("c", {"r": "XFD1"})
        pytest.fail("siguió leyendo después del tope")
    monkeypatch.setattr(ET, "iterparse", eventos)
    assert _medida_hoja(b"sintetico")[0] == 16384
    assert fuentes[0].closed


@pytest.mark.parametrize("celda", [b"<c r='XFD1'", b'<c r="A1" invalido='])
def test_xml_de_hoja_rechazado_devuelve_400_sin_abrir(celda, monkeypatch):
    import openpyxl
    original = _libro([["sintetico"]])
    salida = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as entrada, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                datos = datos.replace(b'<c r="A1"', celda)
            z.writestr(info, datos)
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *a, **k: pytest.fail("abrió el libro"))
    r = TestClient(main.app).post("/upload_excel_v2/", files={"file": ("sintetico.xlsx", salida.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 400, r.text[:300]
    assert r.json()["detail"]


@pytest.mark.parametrize("ref", [b"ref='C2:C3'", b'ref = "C2:C3"', b"ref='&#67;2:C3'"])
def test_combinada_xml_valido_conserva_origen(ref):
    original = _con_combinadas_crudas(_libro([ENCABEZADO, ["84713000", "Equipo", "China", 1, 2, 3], ["84713000", "Otro", None, 1, 2, 3]]), ["C2:C3"])
    salida = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as entrada, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                datos = datos.replace(b'ref="C2:C3"', ref)
            z.writestr(info, datos)
    r = _subir(salida.getvalue())
    assert r.status_code == 200, r.text[:300]
    assert [item["origen"] for item in r.json()["items"]] == ["CN", "CN"]


def test_filas_numericas_excesivas_se_rechazan_antes_de_pandas(monkeypatch, tmp_path):
    filas = [ENCABEZADO] + [["84713000", "Equipo", "China", 1, 2, 3]] * 35
    ruta = tmp_path / "sintetico.xlsx"
    ruta.write_bytes(_libro(filas))
    monkeypatch.setattr(main, "_MAX_FILAS_EXCEL", 3)
    monkeypatch.setattr(main.pd, "read_excel", lambda *a, **k: pytest.fail("abrió pandas antes de rechazar las filas"))
    from fastapi import HTTPException
    with pytest.raises(HTTPException, match="máximo de 3 filas"):
        main._leer_excel_ruta(str(ruta), "openpyxl")


def test_guardia_filas_no_cuenta_huecos_ni_filas_sin_valores(tmp_path, monkeypatch):
    filas = [[99]] * 29 + [ENCABEZADO]
    for _ in range(3):
        filas += [["84713000", "Equipo", "China", 1, 2, 3]] + [[None] * 6] * 40
    ruta = tmp_path / "sintetico.xlsx"
    ruta.write_bytes(_libro(filas))
    monkeypatch.setattr(main, "_MAX_FILAS_EXCEL", 3)
    df = main._leer_excel_ruta(str(ruta), "openpyxl")
    assert len(df) == 3
    assert list(df.index) == [29, 70, 111]



def test_guardia_filas_ignora_extensiones_de_namespace_ajeno():
    original = _libro([ENCABEZADO, ["84713000", "Equipo", "China", 1, 2, 3]])
    salida = io.BytesIO()
    extension = b"<extLst xmlns:q='urn:extension'><q:extra>" + b"<q:row><q:c><q:v>1</q:v></q:c></q:row>" * 40 + b"</q:extra></extLst>"
    with zipfile.ZipFile(io.BytesIO(original)) as entrada, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            datos = entrada.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                datos = datos.replace(b"</worksheet>", extension + b"</worksheet>")
            z.writestr(info, datos)
    _, combinadas = main._xlsx_solo_primera_hoja(salida.getvalue(), max_filas=1)
    assert combinadas == []
