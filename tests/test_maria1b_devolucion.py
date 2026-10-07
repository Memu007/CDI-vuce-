"""Devolución de MARIA-1b (2026-10-07, REPRODUCCION-MARIA-1b-2026-10-07.md).

1. NaN e inf no dejan generar: en cantidad, valor, peso, flete, seguro y
   gastos frenan con el mismo error que un monto inválido, y
   /api/validate/smart no da 500.
2. Mirar las otras hojas del Excel no traba la lectura: tiene un presupuesto
   que corta la lectura (no sólo la espera), y si no se pudo mirar todo, el
   semáforo lo dice.
3. El CUIT, sólo con dígitos 0-9.
4. Toda moneda que no sea DOL avisa (no frena).
5. D22 (a): /generate_maria_export limpia los textos como /generate_maria.
"""
import asyncio
import functools
import io
import time
import zipfile

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests.test_generar_maria_txt import GOLDEN_INPUTS
from tests.test_maria1b_controles import CUIT_VALIDO, USUARIO, _entorno, _errores, _esperado, _generar  # noqa: F401


# ---------------------------------------------------------------- 1. NaN e inf

NO_FINITOS = [float("nan"), float("inf")]


@pytest.mark.parametrize("valor", NO_FINITOS, ids=["nan", "inf"])
@pytest.mark.parametrize("cambio, mensaje", [
    ("cantidad", "Item 1: Cantidad inválida"),
    ("valor_unitario", "Item 1: Valor inválido"),
    ("valor_total", "Item 1: Valor inválido"),
    ("peso_kg", "Item 1: Peso inválido"),
    ("peso_unitario", "Item 1: Peso inválido"),
])
def test_nan_o_inf_en_un_producto_no_dejan_generar(valor, cambio, mensaje):
    r = _generar(item={cambio: valor})
    assert mensaje in _errores(r)


@pytest.mark.parametrize("valor", NO_FINITOS, ids=["nan", "inf"])
@pytest.mark.parametrize("campo, nombre", [
    ("flete", "Flete"), ("seguro", "Seguro"),
    ("gastos_fob", "Gastos"), ("gastos_anteriores_fob", "Gastos"),
])
def test_nan_o_inf_en_la_cabecera_no_dejan_generar(valor, campo, nombre):
    incoterm = "EXW" if campo == "gastos_anteriores_fob" else GOLDEN_INPUTS["incoterm"]
    r = _generar(**{campo: valor, "incoterm": incoterm})
    assert r.status_code == 400, r.text[:300]
    assert nombre in str(r.json()["detail"]), r.json()


@pytest.mark.parametrize("valor", NO_FINITOS, ids=["nan", "inf"])
def test_la_validacion_previa_con_nan_o_inf_no_da_500(valor):
    items = [{"pieza": "84798999900H", "descripcion": "MAQUINA DEMO", "origen": "AR",
              "cantidad": valor, "valor_unitario": valor, "peso_unitario": valor}]
    r = TestClient(main.app).post("/api/validate/smart", json={
        "items": items,
        "operacion": {"moneda": "DOL", "incoterm": "FOB", "comprador_cuit": CUIT_VALIDO,
                      "flete": valor, "seguro": valor}})
    assert r.status_code == 200, r.text[:300]
    errores = " | ".join(r.json()["errores"])
    for parte in ("Cantidad inválida", "Valor inválido", "Peso inválido", "Flete", "Seguro"):
        assert parte in errores, errores


def test_una_descripcion_que_dice_nan_o_infinity_no_es_un_monto():
    items = [{"pieza": "84798999900H", "descripcion": "Infinity", "origen": "AR",
              "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}]
    r = TestClient(main.app).post("/api/validate/smart", json={
        "items": items, "operacion": {"moneda": "DOL", "incoterm": "FOB", "comprador_cuit": CUIT_VALIDO}})
    assert r.status_code == 200, r.text[:300]
    assert not any("inválid" in e for e in r.json()["errores"]), r.json()["errores"]
    assert _generar(item={"descripcion": "nan infinity demo"}).status_code == 200


# ---------------------------------------------------------------- 3. CUIT

@pytest.mark.parametrize("cuit", [
    "３０９９９９９９９９５",                     # ancho completo
    "٣٠٩٩٩٩٩٩٩٩٥",                               # arábigos
    "30999999９95",                               # uno solo
])
def test_cuit_con_digitos_que_no_son_0_a_9_no_deja_generar(cuit):
    assert "CUIT del importador" in _errores(_generar(comprador_cuit=cuit))


def test_cuit_con_digitos_raros_tampoco_pasa_la_validacion_previa():
    from proyecto_maria.core.controles_maria import cuit_valido
    assert cuit_valido(CUIT_VALIDO)
    assert not cuit_valido("３０９９９９９９９９５")


# ---------------------------------------------------------------- 4. moneda

@pytest.mark.parametrize("moneda", ["EUR", "BRL", "CNY", "XYZ"])
def test_toda_moneda_que_no_es_dol_avisa_y_deja_generar(moneda):
    r = _generar(moneda=moneda)
    assert r.status_code == 200, r.text[:300]
    avisos = " | ".join(r.json()["warnings"])
    assert f"«{moneda}»" in avisos and "DOL" in avisos and "despachante" in avisos, avisos


def test_dol_no_avisa():
    r = _generar()
    assert r.status_code == 200, r.text[:300]
    assert not any("moneda" in a.lower() for a in r.json()["warnings"]), r.json()["warnings"]
    assert r.json()["content"] == _esperado()


# ---------------------------------------------------------------- 5. D22

EXPORT = dict(
    operation_id="EXP001",
    items=[{"ncm": "84798999900H", "descripcion": "MAQUINA DEMO", "cantidad": 1,
            "valor_unitario": 5000, "peso_kg": 1220}],
    cuit_exportador="20111111112", exportador_nombre="EXPORTADORA DEMO",
    comprador_nombre="COMPRADOR DEMO", comprador_id="X1",
)


@pytest.mark.parametrize("campo", ["exportador_nombre", "comprador_nombre", "comprador_id", "descripcion"])
def test_la_exportacion_tampoco_mete_lineas_ni_igual(campo):
    pedido = {**EXPORT, "items": [dict(EXPORT["items"][0])]}
    malo = "ACME\r\nCDDTINCOTE=EXW X=1"
    if campo == "descripcion":
        pedido["items"][0]["descripcion"] = malo
    else:
        pedido[campo] = malo
    r = TestClient(main.app).post("/generate_maria_export", json=pedido)
    assert r.status_code == 200, r.text[:300]
    lineas = r.json()["content"].replace("\r\n", "\n").split("\n")
    assert sum(l.startswith("CDDTINCOTE=") for l in lineas) == 1, lineas
    assert not any(l.startswith("X=") for l in lineas)
    assert all(l.count("=") <= 1 for l in lineas), [l for l in lineas if l.count("=") > 1]
    assert " " not in r.json()["content"]


# ---------------------------------------------------------------- 2. otras hojas

@functools.lru_cache(maxsize=None)
def _libro_armado(hojas: int = 50, filas: int = 1000, columnas: int = 60,
                  declarar_medida: bool = True) -> bytes:
    """Un .xlsx armado a mano, como el de la reproducción de la PM: la primera
    hoja con un producto y `hojas` más con `filas` x `columnas` celdas que
    apuntan todas a un mismo texto de 32 000 espacios (en blanco, pero caro de
    mirar celda por celda). Unos 90 MB descomprimido."""
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    total = hojas + 1
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                             for i in range(1, total + 1))
                   + '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr("xl/workbook.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><workbook {ns} {rel}><sheets>'
                   + "".join(f'<sheet name="Hoja{i}" sheetId="{i}" r:id="rId{i}"/>' for i in range(1, total + 1))
                   + '</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                             for i in range(1, total + 1))
                   + f'<Relationship Id="rId{total + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
                   + '</Relationships>')
        z.writestr("xl/sharedStrings.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><sst {ns} count="1" uniqueCount="1">'
                   f'<si><t xml:space="preserve">{" " * 32_000}</t></si></sst>')

        def celda(ref, texto):
            return f'<c r="{ref}" t="inlineStr"><is><t>{texto}</t></is></c>'

        encabezado = ["NCM", "Descripcion", "Pais de origen", "Cantidad", "Precio Unitario", "Peso Neto"]
        fila2 = ["84798999900H", "MAQUINA DEMO", "Argentina"]
        primera = ('<row r="1">' + "".join(celda(f"{chr(65 + i)}1", t) for i, t in enumerate(encabezado)) + "</row>"
                   + '<row r="2">' + "".join(celda(f"{chr(65 + i)}2", t) for i, t in enumerate(fila2))
                   + '<c r="D2"><v>1</v></c><c r="E2"><v>5000</v></c><c r="F2"><v>1220</v></c></row>')
        z.writestr("xl/worksheets/sheet1.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><worksheet {ns}><sheetData>{primera}</sheetData></worksheet>')

        def col(n):
            letras = ""
            while n:
                n, r = divmod(n - 1, 26)
                letras = chr(65 + r) + letras
            return letras

        letras = [col(c) for c in range(1, columnas + 1)]
        cuerpo = "".join(f'<row r="{f}">' + "".join(f'<c r="{l}{f}" t="s"><v>0</v></c>' for l in letras) + "</row>"
                         for f in range(1, filas + 1))
        # Con la medida declarada: sin ella, openpyxl recorre cada hoja entera
        # para medirla al validar y al leer la primera (D26), y esta prueba es
        # sobre mirar las otras hojas.
        medida = f'<dimension ref="A1:{letras[-1]}{filas}"/>' if declarar_medida else ""
        hoja = (f'<?xml version="1.0" encoding="UTF-8"?><worksheet {ns}>{medida}'
                f'<sheetData>{cuerpo}</sheetData></worksheet>')
        for i in range(2, total + 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", hoja)
    return buf.getvalue()


def _libro_normal(hojas: dict) -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for nombre, filas in hojas.items():
        ws = wb.create_sheet(nombre)
        for fila in filas:
            ws.append(fila)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


FILAS = [["NCM", "Descripcion", "Pais de origen", "Cantidad", "Precio Unitario", "Peso Neto"],
         ["84798999900H", "MAQUINA DEMO", "Argentina", 1, 5000, 1220]]


def _subir(contenido: bytes):
    return TestClient(main.app).post("/upload_excel_v2/", files={"file": ("factura.xlsx", contenido)})


def test_mirar_las_otras_hojas_de_un_libro_armado_corta_solo():
    """La lectura misma se corta (no sólo la espera): el hilo queda libre."""
    ruta = "/tmp/_libro_armado_maria1b.xlsx"
    with open(ruta, "wb") as f:
        f.write(_libro_armado())
    t0 = time.monotonic()
    nombres, completo = main._otras_hojas_con_datos(ruta, "openpyxl")
    assert time.monotonic() - t0 < 6, "mirar las otras hojas no cortó"
    assert nombres == [] and completo is False


def test_un_libro_armado_dice_que_no_se_revisaron_todas_las_hojas():
    r = _subir(_libro_armado())
    assert r.status_code == 200, r.text[:300]
    assert r.json()["operacion"].get("hojas_excel_sin_revisar") is True, r.json()["operacion"]


def test_un_libro_normal_se_revisa_entero():
    r = _subir(_libro_normal({"Factura": FILAS, "Notas": [["comentario"]], "Vacia": []}))
    assert r.status_code == 200, r.text[:300]
    op = r.json()["operacion"]
    assert op.get("hojas_excel_sin_leer") == ["Notas"], op
    assert "hojas_excel_sin_revisar" not in op, op


def test_si_mirar_las_otras_hojas_falla_el_semaforo_lo_dice(monkeypatch):
    def _falla(*a):
        raise RuntimeError("libro raro")
    monkeypatch.setattr(main, "_otras_hojas_con_datos", _falla)
    r = _subir(_libro_normal({"Factura": FILAS, "Notas": [["x"]]}))
    assert r.status_code == 200, r.text[:300]
    assert r.json()["operacion"].get("hojas_excel_sin_revisar") is True


def test_dos_libros_armados_no_dejan_sin_lectura_a_una_subida_normal():
    """El criterio de la devolución: dos libros armados y una subida normal
    detrás; la normal no da 504 y sale en poco tiempo."""
    import httpx

    armado = _libro_armado()
    normal = _libro_normal({"Factura": FILAS})

    async def _todo():
        transporte = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test", timeout=300) as c:
            def subir(contenido):
                return c.post("/upload_excel_v2/", files={"file": ("factura.xlsx", contenido)})
            pesadas = [asyncio.create_task(subir(armado)) for _ in range(2)]
            await asyncio.sleep(0.5)
            t0 = time.monotonic()
            r = await subir(normal)
            dt = time.monotonic() - t0
            otras = await asyncio.gather(*pesadas)
            return r, dt, otras

    r, dt, otras = asyncio.run(_todo())
    assert r.status_code == 200, f"la subida normal dio {r.status_code} a los {dt:.1f} s: {r.text[:200]}"
    for o in otras:
        assert o.status_code == 200, o.text[:300]
