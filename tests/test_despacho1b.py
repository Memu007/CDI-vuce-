"""DESPACHO-1b: leer los productos de un despacho para el catálogo (2026-10-28).

- Por renglón (ítem o subítem): posición SIM, descripción, sufijos de valor,
  origen, unidad, cantidad, valor unitario y kilo neto. Se lee por rótulo, no
  por posición; números con la forma `1.234,56`; con unidad SUBITEM, un
  renglón por subítem.
- Lo que no se encuentra queda marcado en `faltantes` y no se rellena.
- Un PDF escaneado da un aviso y no devuelve renglones.
- Se revisa y se guarda en el catálogo de ese cliente; un cliente ajeno da el
  404 de siempre. Nunca arma una operación ni un TXT.
- El lector de facturas sigue rechazando los despachos.

El despacho es sintético, armado acá con la forma de
`docs/pm/DESPACHOS-FORMA.md` y valores inventados."""
import asyncio
import io
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select

from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import ClientProductHistory, Operation


# --- Un PDF mínimo con texto en columnas ------------------------------------

def _pdf(paginas, a_unicode=None):
    """`paginas`: lista de hojas; cada hoja, lista de líneas; cada línea, lista
    de (columna, texto). Courier 9: cada columna mide 5,4 puntos. `a_unicode`:
    {byte: código Unicode en hexa} que la fuente dice para esos bytes."""
    objs = []

    def add(b):
        objs.append(b)
        return len(objs)

    extra = b""
    if a_unicode:
        cmap = (b"/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
                b"/CMapName /X def /CMapType 2 def\n1 begincodespacerange <00> <FF> endcodespacerange\n"
                b"%d beginbfchar\n" % len(a_unicode)
                + b"".join(b"<%02X> <%s>\n" % (k, v.encode()) for k, v in a_unicode.items())
                + b"endbfchar\nendcmap end end")
        extra = b" /ToUnicode %d 0 R" % add(b"<< /Length %d >>\nstream\n" % len(cmap) + cmap + b"\nendstream")
    fuente = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding%s >>" % extra)
    raiz = add(b"")
    hojas = []
    for lineas in paginas:
        ops = []
        for n, linea in enumerate(lineas):
            y = 570 - 11 * n
            for col, texto in linea:
                s = texto.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
                ops.append(b"BT /F1 9 Tf %.1f %d Td (" % (20 + 5.4 * col, y) + s + b") Tj ET")
        data = b"\n".join(ops)
        c = add(b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream")
        hojas.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 842 595] "
                         b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>" % (raiz, fuente, c)))
    objs[raiz - 1] = (b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % h for h in hojas)
                      + b"] /Count %d >>" % len(hojas))
    catalogo = add(b"<< /Type /Catalog /Pages %d 0 R >>" % raiz)
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, catalogo, xref)
    return out


def _fila(*celdas, ancho=None):
    """Celdas (rótulo, valor) en columnas consecutivas. Devuelve la línea de
    rótulos y la de valores, con cada valor debajo de su rótulo."""
    rotulos, valores, col = [], [], 0
    for rotulo, valor in celdas:
        rotulos.append((col, rotulo))
        if valor:
            valores.append((col, valor))
        col += (ancho or max(len(rotulo), len(valor or "")) + 3)
    return [rotulos, valores]


def _encabezado():
    return [[(0, "SUBREGIMEN: IMPORTACION A CONSUMO CON DOCUMENTO DE TRANSPORTE")],
            *_fila(("Aduana", "001 BUENOS AIRES"), ("Oficialización", "01/01/2026"),
                   ("Año / Ad. / Tipo / NºReg. / DC", "26 001 IC04 999999 Z"), ("Fojas", "1")), []]


def _pie():
    return [[], [(0, "Generado por DUX")], [(0, "Firma y Sello Despachante de Aduana")]]


def _caratula(orden_inverso=False):
    fob = [("FOB Total", "1.234,50"), ("Divisa", "EUR")]
    flete = [("Flete Total", "150,00"), ("Divisa", "USD")]
    plata = flete + fob if orden_inverso else fob + flete
    return [
        *_fila(("Importador / Exportador", "IMPORTADORA INVENTADA SA"), ("CUIT Nº", "30-00000000-0"),
               ("Despachante de Aduana", "DESPACHANTE INVENTADO"), ("CUIT Nº", "20-00000000-0")),
        *_fila(("Vía", "MARITIMA"), ("Documento de Transporte", "BL INVENTADO 1"),
               ("Nombre del Transporte", "BARCO INVENTADO")),
        *_fila(("Aduana Destino / Salida", "001"), ("Cond. Venta", "FOB"), *plata),
        [],
    ]


def _item(numero, posicion, kilo, origen, unidad_estado, descripcion, unidad, cantidad,
          unitario, sufijos, orden_inverso=False):
    a = [("Nº Item", numero), ("Tipo", "IC"), ("Posición SIM / Código AFIP", posicion),
         ("Lista", ""), ("Estado", "NUEVO SIN USO IMPORTADO")]
    b = [("Total Kg. Neto", kilo), ("Origen Pais / Provincia", origen),
         ("Pais de Procedencia / Destino", origen), ("Unidad / Estado", unidad_estado),
         ("Cantidad Unidades Estadísticas", cantidad)]
    v = [("Unitario en Divisa", unitario), ("Unidad", unidad), ("Cantidad Unidades", cantidad),
         ("Ajuste a Incluir en Divisa", "0,00"), ("Ajuste a Deducir en Divisa", "0,00")]
    if orden_inverso:
        a = [a[0]] + a[1:][::-1]
        b, v = b[::-1], v[::-1]
    lineas = [[(0, "DECLARACION DE LA MERCADERIA")], *_fila(*a), *_fila(*b)]
    lineas += [[(0, d)] for d in descripcion]
    lineas += [[(0, "VALOR MERCADERIA")], *_fila(*v)]
    lineas += [[(0, "VALOR EN ADUANA")],
               *_fila(("FOB Total en Divisa", "999,99"), ("FOB Total en Dólar", "999,99"))]
    if sufijos:
        lineas += [[(0, "Sufijos de valor:")], *[[(0, s)] for s in sufijos]]
    return lineas + [[]]


def _subitem(numero, kilo, descripcion, unitario, cantidad, sufijos):
    celdas = [("Nº Subitem", numero)]
    if kilo:
        celdas.append(("Total Kg. Neto", kilo))
    lineas = [*_fila(*celdas)]
    lineas += [[(0, d)] for d in descripcion]
    lineas += [[(0, "VALOR MERCADERIA")],
               *_fila(("Unitario en Divisa", unitario), ("Unidad", "UNIDAD"),
                      ("Cantidad Unidades", cantidad))]
    lineas += [[(0, "Sufijos de valor:")], *[[(0, s)] for s in sufijos]]
    return lineas + [[]]


def _despacho(orden_inverso=False):
    """Dos ítems: el 1, solo; el 2, con dos subítems, y el segundo sin kilo
    neto. FOB en euros y flete en dólares; «Las dem?s» con la tilde rota; un
    código de artículo con espacios."""
    hoja1 = [*_encabezado(), *_caratula(orden_inverso),
             *_item("0001", "8471.30.12.900W", "1.234,50", "310 CHINA", "07 NUEVO",
                    ["Las dem?s maquinas automaticas para tratamiento de datos",
                     "NOTEBOOK INVENTADA DE TIPO PORTATIL, UNIDAD DE PROCESO"],
                    "UNIDAD", "1.000,00", "1.234,56",
                    ["AA(ACME) = MARCA", "AI(XZ 400 B) = CODIGO", "PB00 = Ninguno"],
                    orden_inverso=orden_inverso),
             *_pie()]
    hoja2 = [*_encabezado(),
             *_item("0002", "3926.90.90.100K", "30,00", "203 BRASIL", "SUBITEM",
                    ["Las demas manufacturas de plastico"], "SUBITEM", "2,00", "0,00", [],
                    orden_inverso=orden_inverso),
             *_subitem("0001", "12,50", ["TAPA INVENTADA AZUL"], "5,25", "100,00",
                       ["AA(OTRA MARCA) = MARCA", "AI(TP-1) = CODIGO"]),
             *_subitem("0002", None, ["TAPA INVENTADA ROJA"], "4,75", "50,00",
                       ["AI(TP-2) = CODIGO", "PC01 = AUTOADHESIVO EN UNA CARA"]),
             *_pie()]
    return _pdf([hoja1, hoja2])


def _pdf_sin_texto():
    from pypdf import PdfWriter
    w = PdfWriter()
    w.add_blank_page(width=842, height=595)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _pdf_con_texto(lineas):
    return _pdf([[[(0, l)] for l in lineas]])


def _leer(data=None):
    from proyecto_maria.core.despacho_lector import leer_despacho
    return leer_despacho(_despacho() if data is None else data)


# --- El lector --------------------------------------------------------------

def test_lee_cada_rotulo_del_item():
    r = _leer()
    assert r["sin_texto"] is False
    assert r["divisa"] == "EUR"
    uno = r["renglones"][0]
    assert (uno["item"], uno["subitem"]) == ("0001", None)
    assert uno["posicion_sim"] == "8471.30.12.900W"
    assert uno["descripcion"] == ("Las dem?s maquinas automaticas para tratamiento de datos "
                                  "NOTEBOOK INVENTADA DE TIPO PORTATIL, UNIDAD DE PROCESO")
    assert (uno["origen"], uno["origen_leido"]) == ("CN", "310 CHINA")
    assert uno["unidad"] == "UNIDAD"
    assert uno["cantidad"] == 1000.0
    assert uno["valor_unitario"] == 1234.56
    assert uno["kilo_neto"] == 1234.5
    assert uno["faltantes"] == [] and uno["heredados"] == []


def test_con_subitems_sale_un_renglon_por_subitem():
    r = _leer()
    assert [(x["item"], x["subitem"]) for x in r["renglones"]] == [
        ("0001", None), ("0002", "0001"), ("0002", "0002")]
    azul, roja = r["renglones"][1:]
    assert (azul["descripcion"], azul["valor_unitario"], azul["cantidad"], azul["unidad"]) == (
        "TAPA INVENTADA AZUL", 5.25, 100.0, "UNIDAD")
    assert (roja["descripcion"], roja["valor_unitario"], roja["cantidad"]) == (
        "TAPA INVENTADA ROJA", 4.75, 50.0)
    # La posición y el origen son del ítem, y se dice que se heredaron.
    for sub in (azul, roja):
        assert sub["posicion_sim"] == "3926.90.90.100K"
        assert sub["origen"] == "BR"
        assert sub["heredados"] == ["posicion_sim", "origen"]
    assert azul["kilo_neto"] == 12.5


def test_sufijos_con_y_sin_parentesis():
    uno, azul, roja = _leer()["renglones"]
    assert uno["sufijos"] == [
        {"codigo": "AA", "valor": "ACME", "texto": "AA(ACME)", "significado": "MARCA"},
        {"codigo": "AI", "valor": "XZ 400 B", "texto": "AI(XZ 400 B)", "significado": "CODIGO"},
        {"codigo": "PB", "valor": "00", "texto": "PB00", "significado": "Ninguno"},
    ]
    assert [s["texto"] for s in azul["sufijos"]] == ["AA(OTRA MARCA)", "AI(TP-1)"]
    assert [s["texto"] for s in roja["sufijos"]] == ["AI(TP-2)", "PC01"]
    assert roja["sufijos"][1]["significado"] == "AUTOADHESIVO EN UNA CARA"


def test_lo_que_falta_queda_marcado_y_no_se_rellena():
    roja = _leer()["renglones"][2]
    # El ítem 2 dice 30,00 kg y el otro subítem 12,50: ninguno se copia.
    assert roja["kilo_neto"] is None
    assert roja["faltantes"] == ["kilo_neto"]


def test_rotulos_en_otro_orden_leen_lo_mismo():
    assert _leer(_despacho(orden_inverso=True)) == _leer()


def test_la_divisa_es_la_del_fob_y_no_la_del_flete():
    assert _leer(_despacho(orden_inverso=True))["divisa"] == "EUR"


def test_tilde_rota_avisa_y_la_descripcion_queda_como_vino():
    uno = _leer()["renglones"][0]
    assert uno["descripcion"].startswith("Las dem?s ")
    assert any("no se pudieron leer" in a for a in uno["avisos"])
    assert not any("no se pudieron leer" in a for a in _leer()["renglones"][1]["avisos"])


@pytest.mark.parametrize("texto, numero", [
    ("1.234,56", 1234.56), ("1.000.000,5", 1000000.5), ("0,00", 0.0), ("12", 12.0),
    ("1.234", 1234.0), ("1,234.56", None), ("12.5", None), ("1.23,4", None), ("", None),
    ("-5,00", None), ("12 kg", None)])
def test_numeros_con_punto_de_miles_y_coma_decimal(texto, numero):
    from proyecto_maria.core.despacho_lector import numero_ar
    assert numero_ar(texto) == numero


def _item_solo(**cambios):
    """El texto de un ítem suelto, con los valores cambiados."""
    v = {"pos": "8471.30.12.900W", "kilo": "10,00", "origen": "310 CHINA", "unitario": "5,00",
         "unidad": "UNIDAD", "cant": "2,00", **cambios}
    return "\n".join([
        "Nº Item    Posición SIM / Código AFIP    Total Kg. Neto    Origen Pais / Provincia",
        f"0001       {v['pos']:<30}{v['kilo']:<18}{v['origen']}",
        "COSA INVENTADA",
        "VALOR MERCADERIA",
        "Unitario en Divisa    Unidad        Cantidad Unidades",
        f"{v['unitario']:<22}{v['unidad']:<14}{v['cant']}",
    ])


def test_un_numero_con_otra_forma_queda_faltante_con_aviso():
    from proyecto_maria.core.despacho_lector import leer_texto
    r = leer_texto(_item_solo(unitario="5.00"))["renglones"][0]
    assert r["valor_unitario"] is None and "valor_unitario" in r["faltantes"]
    assert any("«5.00»" in a for a in r["avisos"])


def test_un_valor_vacio_no_corre_los_de_al_lado():
    # Se lee por rótulo: sin kilo, el origen sigue siendo el origen y el kilo
    # queda faltante (leyendo por posición, el origen caería en el kilo).
    from proyecto_maria.core.despacho_lector import leer_texto
    r = leer_texto(_item_solo(kilo=""))["renglones"][0]
    assert r["kilo_neto"] is None and "kilo_neto" in r["faltantes"]
    assert r["origen"] == "CN" and r["posicion_sim"] == "8471.30.12.900W"
    assert not any("kilo" in a.lower() for a in r["avisos"])


@pytest.mark.parametrize("origen", ["310 BRASIL", "999 ATLANTIDA", "ATLANTIDA"])
def test_origen_que_no_cierra_queda_faltante(origen):
    from proyecto_maria.core.despacho_lector import leer_texto
    r = leer_texto(_item_solo(origen=origen))["renglones"][0]
    assert r["origen"] is None and r["origen_leido"] == origen
    assert "origen" in r["faltantes"]


def test_posicion_rara_queda_faltante():
    from proyecto_maria.core.despacho_lector import leer_texto
    r = leer_texto(_item_solo(pos="84X1.30"))["renglones"][0]
    assert r["posicion_sim"] is None and "posicion_sim" in r["faltantes"]


def test_subitem_declarado_sin_subitems_avisa():
    from proyecto_maria.core.despacho_lector import leer_texto
    r = leer_texto(_item_solo(unidad="SUBITEM"))["renglones"][0]
    assert r["unidad"] is None
    assert any("SUBITEM" in a for a in r["avisos"])


def test_pdf_sin_texto_avisa_y_no_devuelve_renglones():
    r = _leer(_pdf_sin_texto())
    assert r["sin_texto"] is True and r["renglones"] == []
    assert any("escaneado" in a for a in r["avisos"])


def test_pdf_que_no_es_despacho_avisa():
    r = _leer(_pdf_con_texto(["FACTURA COMERCIAL INVENTADA", "Total 100,00"]))
    assert r["renglones"] == [] and r["sin_texto"] is False
    assert any("Nº Item" in a for a in r["avisos"])


def test_pdf_roto_avisa():
    r = _leer(b"%PDF-1.4 esto no es un pdf")
    assert r["renglones"] == [] and r["avisos"]


# --- Leer y guardar en el catálogo del cliente ------------------------------

def _crear_cliente(client, nombre=None):
    r = client.post("/api/clientes", json={
        "nombre": nombre or f"Cliente Inventado D1b {uuid.uuid4().hex[:8]}"})
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _subir(client, cid, data=None):
    return client.post(f"/api/clientes/{cid}/catalogo/despacho/leer",
                       files={"file": ("despacho.pdf", io.BytesIO(_despacho() if data is None else data),
                                       "application/pdf")})


def _guardar(client, cid, renglones, divisa="USD"):
    return client.post(f"/api/clientes/{cid}/catalogo/despacho/guardar",
                       json={"renglones": renglones, "divisa": divisa})


def _catalogo(client, cid):
    r = client.get(f"/api/clientes/{cid}/catalogo/productos")
    assert r.status_code == 200, r.text
    return r.json()["productos"]


def _contar(modelo, **filtro):
    async def _c():
        async with AsyncSessionLocal() as s:
            q = select(func.count()).select_from(modelo)
            for campo, valor in filtro.items():
                q = q.where(getattr(modelo, campo) == valor)
            return (await s.execute(q)).scalar_one()
    return asyncio.run(_c())


def _como_otro(auth_override):
    from proyecto_maria.main import app, get_current_user
    otro = dict(auth_override)
    otro["username"] = otro["effective_owner"] = f"otro_dueno_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: otro
    return otro


def _volver(auth_override):
    from proyecto_maria.main import app, get_current_user
    app.dependency_overrides[get_current_user] = lambda: auth_override


def test_leer_devuelve_los_renglones_y_no_guarda_nada(auth_override, client):
    cid = _crear_cliente(client)
    operaciones = _contar(Operation)
    r = _subir(client, cid)
    assert r.status_code == 200, r.text
    assert r.json()["renglones"] == _leer()["renglones"]
    assert r.json()["divisa"] == "EUR"
    assert _contar(ClientProductHistory, client_id=cid) == 0
    assert _contar(Operation) == operaciones


def test_leer_un_escaneado_avisa(auth_override, client):
    cid = _crear_cliente(client)
    r = _subir(client, cid, _pdf_sin_texto())
    assert r.status_code == 200, r.text
    assert r.json()["sin_texto"] is True and r.json()["renglones"] == []


def test_leer_rechaza_lo_que_no_es_pdf(auth_override, client):
    cid = _crear_cliente(client)
    r = _subir(client, cid, b"no soy un pdf")
    assert r.status_code == 400, r.text


def test_guardar_lo_revisado_queda_en_el_catalogo_del_cliente(auth_override, client):
    cid = _crear_cliente(client)
    renglones = _subir(client, cid).json()["renglones"]
    renglones[2]["kilo_neto"] = 5.0  # la persona completa el faltante
    operaciones = _contar(Operation)
    r = _guardar(client, cid, renglones)
    assert r.status_code == 200, r.text
    assert r.json()["guardados"] == 3
    productos = {p["descripcion"]: p for p in _catalogo(client, cid)}
    assert set(productos) == {
        "Las dem?s maquinas automaticas para tratamiento de datos NOTEBOOK INVENTADA DE TIPO PORTATIL, UNIDAD DE PROCESO",
        "TAPA INVENTADA AZUL", "TAPA INVENTADA ROJA"}
    azul = productos["TAPA INVENTADA AZUL"]
    assert azul["ncm"] == "39269090"
    assert azul["origen"] == "BR"
    assert azul["valor_unitario_avg"] == 5.25
    assert azul["cantidad_avg"] == 100.0
    assert azul["peso_unitario_avg"] == pytest.approx(0.125)
    assert productos["TAPA INVENTADA ROJA"]["peso_unitario_avg"] == pytest.approx(0.1)
    assert _contar(Operation) == operaciones


def test_guardar_sin_kilo_no_inventa_el_peso(auth_override, client):
    cid = _crear_cliente(client)
    roja = _subir(client, cid).json()["renglones"][2]
    assert _guardar(client, cid, [roja]).status_code == 200
    assert _catalogo(client, cid)[0]["peso_unitario_avg"] in (0, 0.0, None)


@pytest.mark.parametrize("cambio, problema", [
    ({"descripcion": "  "}, "Falta la descripción."),
    ({"posicion_sim": None}, "Falta la posición SIM"),
    ({"posicion_sim": "8471"}, "Falta la posición SIM"),
    ({"origen": "ZZ"}, "No reconozco el origen"),
    ({"origen": "CHINA"}, "No reconozco el origen"),
    ({"cantidad": "10"}, "La cantidad no es un número."),
    ({"valor_unitario": -1}, "El valor unitario tiene que ser un número positivo."),
    ({"kilo_neto": True}, "El kilo neto no es un número."),
])
def test_guardar_es_todo_o_nada(auth_override, client, cambio, problema):
    cid = _crear_cliente(client)
    renglones = _subir(client, cid).json()["renglones"]
    renglones[1].update(cambio)
    r = _guardar(client, cid, renglones)
    assert r.status_code == 422, r.text
    assert r.json()["code"] == "renglones_incompletos"
    assert [e["renglon"] for e in r.json()["errores"]] == [2]
    assert any(p.startswith(problema) for p in r.json()["errores"][0]["problemas"])
    assert _contar(ClientProductHistory, client_id=cid) == 0


@pytest.mark.parametrize("cuerpo", [{}, {"renglones": []}, {"renglones": "x"}, [1]])
def test_guardar_sin_renglones_da_400(auth_override, client, cuerpo):
    cid = _crear_cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/despacho/guardar", json=cuerpo)
    assert r.status_code in (400, 422), r.text
    assert _contar(ClientProductHistory, client_id=cid) == 0


def test_guardar_mas_del_tope_da_400(auth_override, client):
    from proyecto_maria.core.despacho_lector import MAX_RENGLONES
    cid = _crear_cliente(client)
    uno = _subir(client, cid).json()["renglones"][0]
    r = _guardar(client, cid, [uno] * (MAX_RENGLONES + 1))
    assert r.status_code == 400, r.text
    assert _contar(ClientProductHistory, client_id=cid) == 0


def test_otro_dueno_no_lee_ni_guarda_en_un_cliente_ajeno(auth_override, client):
    cid = _crear_cliente(client)
    renglones = _subir(client, cid).json()["renglones"]
    _como_otro(auth_override)
    try:
        for r in (_subir(client, cid), _guardar(client, cid, renglones)):
            assert r.status_code == 404, r.text
            assert r.json()["detail"] == "Cliente no encontrado"
    finally:
        _volver(auth_override)
    assert _contar(ClientProductHistory, client_id=cid) == 0


def test_guardar_en_un_cliente_no_toca_otro(auth_override, client):
    a, b = _crear_cliente(client), _crear_cliente(client)
    assert _guardar(client, b, _subir(client, b).json()["renglones"]).status_code == 200
    assert _catalogo(client, a) == []
    assert len(_catalogo(client, b)) == 3


def test_nunca_arma_un_txt(auth_override, client, monkeypatch):
    import proyecto_maria.main as main
    monkeypatch.setattr(main, "generate_maria_txt", lambda *a, **k: pytest.fail("armó un TXT"))
    cid = _crear_cliente(client)
    assert _guardar(client, cid, _subir(client, cid).json()["renglones"]).status_code == 200


# --- El lector de facturas sigue rechazando los despachos --------------------

def test_el_lector_de_facturas_sigue_rechazando_el_despacho(auth_override, client, monkeypatch):
    import proyecto_maria.main as main
    from tests.test_doc1_documentos import FACTURA, _respuesta
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(main, "process_pdf", lambda _: _respuesta(dict(FACTURA, tipo="despacho_aduanero")))
    monkeypatch.setattr("proyecto_maria.core.ai_quota.enforce_pdf_quota", lambda _: None)
    monkeypatch.setattr("proyecto_maria.core.despacho_lector.leer_despacho",
                        lambda _: pytest.fail("el lector de facturas usó el de despachos"))
    monkeypatch.setattr("proyecto_maria.core.despacho_lector.leer_despacho_aparte",
                        lambda *_: pytest.fail("el lector de facturas usó el de despachos"))
    r = client.post("/upload_pdf/public",
                    files={"file": ("despacho.pdf", io.BytesIO(_despacho()), "application/pdf")})
    assert r.status_code == 422, r.text
    assert r.json()["code"] == "documento_no_admitido"
    assert "items" not in r.json()


# --- D41: las tres medias de la revisión (2026-10-28) ----------------------

@pytest.mark.parametrize("rotulos, rechaza", [(40, False), (41, True)])
def test_una_linea_con_mas_de_40_rotulos_no_se_lee(rotulos, rechaza):
    """Una línea con miles de rótulos trababa el lector de PDF que comparten
    todos. Ahora la cantidad de rótulos tiene tope: el tope se prueba, no un
    tiempo."""
    from proyecto_maria.core.despacho_lector import leer_texto
    texto = "Nº Item " + "Tipo " * (rotulos - 1) + "\n" + "0001  " + "x  " * (rotulos - 1) + "\n"
    leido = leer_texto(texto)
    aviso = "Una línea tiene más de 40 rótulos: no parece un despacho."
    assert (leido["avisos"] == [aviso]) is rechaza, leido["avisos"]
    assert len(leido["renglones"]) == (0 if rechaza else 1)


def test_muchos_rotulos_reparten_igual_que_pocos():
    """El arreglo no cambia a qué rótulo va cada valor: uno que asoma dos
    columnas a la izquierda sigue en la suya, y uno que pisa la columna
    siguiente con un solo espacio se corta donde ella empieza."""
    from proyecto_maria.core.despacho_lector import _rotulos_de_linea, _valores_por_columna
    columnas = _rotulos_de_linea(
        "Nº Item    Posición SIM / Código AFIP    Total Kg. Neto    Origen Pais / Provincia")
    assert [c for c, _ in columnas] == [0, 11, 41, 59]

    def linea(*valores):
        texto = ""
        for columna, valor in valores:
            texto = texto.ljust(columna) + valor
        return texto

    esperado = {"Nº Item": "0001", "Posición SIM / Código AFIP": "8471.30.12.000W",
                "Total Kg. Neto": "12,500", "Origen Pais / Provincia": "310 BRASIL"}
    # El kilo asoma dos a la izquierda de su rótulo.
    assert _valores_por_columna(
        linea((0, "0001"), (11, "8471.30.12.000W"), (39, "12,500"), (59, "310 BRASIL")),
        columnas) == esperado
    # El kilo llega pegado al origen, con un solo espacio en la columna 58.
    assert _valores_por_columna(
        linea((0, "0001"), (11, "8471.30.12.000W"), (52, "12,500 310 BRASIL")),
        columnas) == esperado


@pytest.mark.parametrize("kilo, cantidad", [(1.0, 1e-320), (9e11, 1e-300), (1e11, 1e-5)])
def test_un_peso_por_unidad_infinito_no_se_guarda(auth_override, client, kilo, cantidad):
    """Kilo dividido cantidad no puede dar infinito: antes se guardaba y el
    catálogo del cliente daba 500 (infinito no es JSON). Tampoco más del tope
    de cualquier número del renglón (1e16 con el último par)."""
    cid = _crear_cliente(client)
    renglones = _subir(client, cid).json()["renglones"]
    renglones[1].update(kilo_neto=kilo, cantidad=cantidad)
    r = _guardar(client, cid, renglones)
    assert r.status_code == 422, r.text
    assert [e["renglon"] for e in r.json()["errores"]] == [2]
    assert any(p.startswith("El peso por unidad") for p in r.json()["errores"][0]["problemas"]), r.text
    assert _contar(ClientProductHistory, client_id=cid) == 0
    assert _catalogo(client, cid) == []


def _renglon(descripcion, posicion):
    return {"posicion_sim": posicion, "descripcion": descripcion, "origen": "BR",
            "cantidad": 10.0, "valor_unitario": 2.0, "kilo_neto": 1.0}


def test_guardar_no_funde_productos_con_ncm_distinto(auth_override, client):
    """La misma descripción con otra posición es otro producto: antes el
    respaldo por descripción lo sumaba al de la otra posición, que quedaba con
    su NCM, y «guardados» lo contaba igual."""
    cid = _crear_cliente(client)
    r = _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A"),
                               _renglon("TAPA INVENTADA VERDE", "8471.30.12.000W")])
    assert r.status_code == 200, r.text
    assert r.json()["guardados"] == 2
    productos = _catalogo(client, cid)
    assert sorted((p["ncm"], p["veces_usado"]) for p in productos) == [
        ("39269090", 1), ("84713012", 1)], productos


def test_guardar_no_toca_un_producto_que_ya_estaba_con_otro_ncm(auth_override, client):
    cid = _crear_cliente(client)
    assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")]).status_code == 200
    r = _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "8471.30.12.000W")])
    assert r.status_code == 200, r.text
    productos = {p["ncm"]: p for p in _catalogo(client, cid)}
    assert set(productos) == {"39269090", "84713012"}, productos
    assert productos["39269090"]["veces_usado"] == 1


def test_guardar_con_el_mismo_ncm_sigue_sumando(auth_override, client):
    """El arreglo no cambia lo que ya andaba: misma posición y misma
    descripción es el mismo producto."""
    cid = _crear_cliente(client)
    for _ in range(2):
        assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")]).status_code == 200
    productos = _catalogo(client, cid)
    assert [(p["ncm"], p["veces_usado"]) for p in productos] == [("39269090", 2)], productos


@pytest.mark.parametrize("descripciones", [
    # Las palabras de una letra no cuentan: la similitud da 1,0.
    ("TAPA INVENTADA DE PLASTICO TIPO A", "TAPA INVENTADA DE PLASTICO TIPO B"),
    # La descripción normalizada se corta en 200: el resto no se compara.
    ("LAS DEMAS MANUFACTURAS INVENTADAS " * 7 + "TAPA", "LAS DEMAS MANUFACTURAS INVENTADAS " * 7 + "CAJA"),
], ids=["tipo a y tipo b", "mismo texto largo adelante"])
def test_guardar_no_funde_descripciones_casi_iguales_con_ncm_distinto(auth_override, client, descripciones):
    """En un despacho la posición SIM manda: dos descripciones que el respaldo
    por descripción daría por iguales siguen siendo dos productos."""
    cid = _crear_cliente(client)
    r = _guardar(client, cid, [_renglon(descripciones[0], "3926.90.90.000A"),
                               _renglon(descripciones[1], "8471.30.12.000W")])
    assert r.status_code == 200, r.text
    productos = _catalogo(client, cid)
    assert sorted((p["ncm"], p["veces_usado"]) for p in productos) == [
        ("39269090", 1), ("84713012", 1)], productos


# --- DESPACHO-1b, devolución: cada tope corta antes de gastar --------------

_REPO = Path(__file__).resolve().parents[1]


def _medir_aparte(bomba, *args):
    """Arma la bomba y la lee con `leer_despacho_aparte` en un python nuevo y
    chico: la memoria del proceso que lee se mide sin la de pytest."""
    from tests.pdf_bombas import MEDIR
    r = subprocess.run([sys.executable, "-c", MEDIR, bomba, *map(str, args)], capture_output=True,
                       text=True, cwd=_REPO, timeout=120,
                       env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(_REPO)})
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


solo_linux = pytest.mark.skipif(sys.platform != "linux", reason="el tope de memoria es de Linux")


@solo_linux
def test_hojas_que_se_inflan_se_saltean_sin_gastar_memoria():
    """10 hojas de 70 MB descomprimidos cada una, en un PDF de menos de 1 MB:
    antes la lectura llegaba a 800 MB. Cada hoja corta al pasar el tope de un
    flujo y se avisa; el proceso que lee no pasa de 100 MB."""
    medido = _medir_aparte("hojas_pesadas", 10, 70)
    assert "resultado" in medido, medido
    assert medido["resultado"]["avisos"] == [
        f"No leí la hoja {n}: es demasiado pesada." for n in range(1, 11)], medido
    assert medido["resultado"]["sin_texto"] is False
    assert medido["lector_mb"] < 100, medido


@solo_linux
def test_un_pdf_que_llena_la_memoria_se_rechaza():
    """1000 fuentes de 500 KB: cada flujo pasa el tope por flujo, pero todos
    juntos no. Lo corta el tope de memoria del proceso que lee: se rechaza
    con un aviso y la memoria queda acotada."""
    from proyecto_maria.core.despacho_lector import AVISO_SIN_MEMORIA
    medido = _medir_aparte("muchas_fuentes", 1000, 500)
    assert medido.get("pesado") == AVISO_SIN_MEMORIA, medido
    assert medido["lector_mb"] < 300, medido


def test_una_hoja_pesada_se_saltea_y_las_demas_se_leen():
    from proyecto_maria.core.despacho_lector import texto_del_pdf
    from tests.pdf_bombas import hojas
    texto, avisos = texto_del_pdf(hojas([("HOJA UNO", 0), ("HOJA DOS", 2 << 20), ("HOJA TRES", 0)]))
    assert avisos == ["No leí la hoja 2: es demasiado pesada."]
    assert "HOJA UNO" in texto and "HOJA TRES" in texto and "HOJA DOS" not in texto


def test_mas_de_200_hojas_lee_las_primeras_200():
    from proyecto_maria.core.despacho_lector import texto_del_pdf
    from tests.pdf_bombas import hojas
    texto, avisos = texto_del_pdf(hojas([(f"HOJA {n:03d}", 0) for n in range(1, 202)]))
    assert avisos == ["El PDF tiene 201 hojas: leí las primeras 200."]
    assert "HOJA 200" in texto and "HOJA 201" not in texto


def test_el_texto_de_todas_las_hojas_tiene_tope(monkeypatch):
    from proyecto_maria.core import despacho_lector
    from tests.pdf_bombas import hojas
    data = hojas([("HOJA UNO", 0), ("HOJA DOS", 0), ("HOJA TRES", 0)])
    una, _ = despacho_lector.texto_del_pdf(hojas([("HOJA UNO", 0)]))
    # Entran la primera y la segunda; la tercera pasa del tope.
    monkeypatch.setattr(despacho_lector, "_MAX_TEXTO", 2 * len(una) + 1)
    texto, avisos = despacho_lector.texto_del_pdf(data)
    assert avisos == ["El texto del PDF es demasiado largo: leí hasta la hoja 2."]
    assert "HOJA DOS" in texto and "HOJA TRES" not in texto


@pytest.mark.parametrize("largo, rechaza", [(2000, False), (2001, True)])
def test_una_linea_de_mas_de_2000_caracteres_no_se_lee(largo, rechaza):
    from proyecto_maria.core.despacho_lector import leer_texto
    leido = leer_texto(_item_solo() + "\n" + "X" * largo)
    aviso = "Una línea pasa de 2000 caracteres: no parece un despacho."
    assert (aviso in leido["avisos"]) is rechaza, leido["avisos"]
    assert len(leido["renglones"]) == (0 if rechaza else 1)


@pytest.mark.parametrize("items, avisa", [(500, False), (501, True)])
def test_mas_de_500_items_lee_los_primeros_500(items, avisa):
    from proyecto_maria.core.despacho_lector import leer_texto
    leido = leer_texto("\n".join(_item_solo() for _ in range(items)))
    aviso = "El despacho tiene más de 500 ítems y subítems: leí sólo los primeros 500."
    assert (aviso in leido["avisos"]) is avisa, leido["avisos"]
    assert len(leido["renglones"]) == 500


def test_leer_que_tarda_demasiado_da_504_y_mata_al_lector(auth_override, client, monkeypatch):
    """El proceso que lee se mata al pasar el tiempo: no queda ocupando nada.
    El lector se reemplaza por uno que no termina nunca (validar el PDF,
    antes de leerlo, queda como es)."""
    real = asyncio.create_subprocess_exec
    procesos = []

    async def lector_colgado(*args, **kwargs):
        if args[-1] == "validar":
            return await real(*args, **kwargs)
        proceso = await real(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)
        procesos.append(proceso)
        return proceso

    monkeypatch.setattr(asyncio, "create_subprocess_exec", lector_colgado)
    monkeypatch.setenv("PDF_READ_TIMEOUT_S", "1")
    cid = _crear_cliente(client)
    r = _subir(client, cid)
    assert r.status_code == 504, r.text
    assert r.json()["code"] == "lectura_pdf_demasiado_larga"
    assert len(procesos) == 1 and procesos[0].returncode == -9


@solo_linux
def test_leer_un_pdf_que_llena_la_memoria_avisa(auth_override, client):
    from proyecto_maria.core.despacho_lector import AVISO_SIN_MEMORIA
    from tests.pdf_bombas import muchas_fuentes
    cid = _crear_cliente(client)
    r = _subir(client, cid, muchas_fuentes(1000, 500))
    assert r.status_code == 200, r.text
    assert r.json()["renglones"] == [] and r.json()["avisos"] == [AVISO_SIN_MEMORIA]
    assert r.json()["sin_texto"] is False


@pytest.mark.parametrize("campo", ["cantidad", "valor_unitario", "kilo_neto"])
def test_guardar_un_numero_del_tope_para_arriba_da_422(auth_override, client, campo):
    cid = _crear_cliente(client)
    renglon = _renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")
    renglon[campo] = 1e12
    r = _guardar(client, cid, [renglon])
    assert r.status_code == 422, r.text
    assert r.json()["errores"][0]["problemas"][0].endswith("tiene que ser un número positivo.")
    assert _contar(ClientProductHistory, client_id=cid) == 0


def test_guardar_si_falla_la_base_no_guarda_ninguno(auth_override, client, monkeypatch):
    """El segundo renglón falla al escribir: el primero tampoco queda."""
    from proyecto_maria.services import client_memory
    real = client_memory.upsert_client_product_history
    llamadas = []

    async def falla_el_segundo(*args, **kwargs):
        llamadas.append(kwargs["descripcion"])
        if len(llamadas) == 2:
            raise RuntimeError("la base no anda")
        return await real(*args, **kwargs)

    monkeypatch.setattr(client_memory, "upsert_client_product_history", falla_el_segundo)
    cid = _crear_cliente(client)
    r = _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A"),
                               _renglon("CAJA INVENTADA AZUL", "8471.30.12.000W")])
    assert r.status_code == 500, r.text
    assert len(llamadas) == 2
    assert _contar(ClientProductHistory, client_id=cid) == 0


def test_guardar_saca_el_nul_de_los_textos(auth_override, client):
    """Postgres no acepta NUL en un texto; con el NUL afuera, el origen es
    uno de la tabla."""
    cid = _crear_cliente(client)
    renglon = _renglon("TAPA INVENTADA\x00 VERDE", "3926.90.90.000A")
    renglon["origen"] = "B\x00R"
    r = _guardar(client, cid, [renglon])
    assert r.status_code == 200, r.text
    assert [(p["descripcion"], p["origen"]) for p in _catalogo(client, cid)] == [
        ("TAPA INVENTADA VERDE", "BR")]


def test_guardar_otra_vez_con_peso_no_lo_promedia_con_el_vacio(auth_override, client):
    """Un producto guardado sin peso ni valor, guardado otra vez con 2 kg por
    unidad y 3 de valor, queda con 2 y 3: antes, con 1 y 1,5."""
    cid = _crear_cliente(client)
    sin = _renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")
    sin.update(kilo_neto=None, valor_unitario=None)
    con = _renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")
    con.update(kilo_neto=20.0, valor_unitario=3.0)
    assert _guardar(client, cid, [sin]).status_code == 200
    assert _guardar(client, cid, [con]).status_code == 200
    [producto] = _catalogo(client, cid)
    assert (producto["veces_usado"], producto["peso_unitario_avg"], producto["valor_unitario_avg"]) == (
        2, 2.0, 3.0), producto


# --- DESPACHO-1b, code-review: el tope cuenta renglones, no bloques --------

def _subitem_solo(n=1):
    return "\n".join(["Nº Subitem", f"{n:04d}", f"SUBITEM INVENTADO {n}", "VALOR MERCADERIA",
                      "Unitario en Divisa    Unidad        Cantidad Unidades",
                      "5,00                  UNIDAD        2,00"])


def _item_con_subitems(cuantos=1):
    """Un ítem con subítems: da un renglón por subítem y ninguno propio."""
    return "\n".join([_item_solo(), *(_subitem_solo(n) for n in range(1, cuantos + 1))])


def test_300_items_con_un_subitem_son_300_renglones_sin_aviso():
    """Son 600 bloques pero 300 renglones: antes cortaba a los 250 ítems."""
    from proyecto_maria.core.despacho_lector import leer_texto
    leido = leer_texto("\n".join(_item_con_subitems() for _ in range(300)))
    assert len(leido["renglones"]) == 300
    assert not any("más de 500" in a for a in leido["avisos"]), leido["avisos"]


@pytest.mark.parametrize("solos", [499, 0])
def test_mas_de_500_renglones_con_subitems_lee_los_primeros_500(solos):
    """499 ítems solos y uno con dos subítems, o uno solo con 501 subítems:
    501 renglones."""
    from proyecto_maria.core.despacho_lector import leer_texto
    leido = leer_texto("\n".join([_item_solo()] * solos + [_item_con_subitems(2 if solos else 501)]))
    aviso = "El despacho tiene más de 500 ítems y subítems: leí sólo los primeros 500."
    assert aviso in leido["avisos"], leido["avisos"]
    assert len(leido["renglones"]) == 500


def test_si_la_primera_hoja_pasa_el_tope_del_texto_no_dice_hoja_0(monkeypatch):
    from proyecto_maria.core import despacho_lector
    from tests.pdf_bombas import hojas
    monkeypatch.setattr(despacho_lector, "_MAX_TEXTO", 3)
    texto, avisos = despacho_lector.texto_del_pdf(hojas([("HOJA UNO", 0), ("HOJA DOS", 0)]))
    assert avisos == ["El texto de la primera hoja es demasiado largo: no leí ninguna."]
    assert texto == ""


# Corre en un python nuevo: el lector se reemplaza por uno que escribe
# 300 MB de errores y sale con 1. Imprime el error y la memoria propia: la de
# /proc (VmHWM), porque `ru_maxrss` arranca con la del que lo lanzó (pytest).
_ERRORES_LARGOS = r"""
import asyncio, json, re, sys
from proyecto_maria.core import despacho_lector
real = asyncio.create_subprocess_exec
async def ruidoso(*args, **kwargs):
    codigo = ("import sys\nfor _ in range(300): sys.stderr.write('x' * (1 << 20))\n"
              "sys.stderr.write('FIN DEL ERROR'); sys.exit(1)")
    return await real(sys.executable, "-c", codigo, **kwargs)
asyncio.create_subprocess_exec = ruidoso
try:
    asyncio.run(despacho_lector.leer_despacho_aparte(b"%PDF", 120))
    error = None
except RuntimeError as e:
    error = str(e)
propio_kb = int(re.search(r"VmHWM:\s+(\d+)", open("/proc/self/status").read()).group(1))
print(json.dumps({"error": error, "propio_mb": propio_kb // 1024}))
"""


@solo_linux
def test_los_errores_del_lector_no_se_juntan_enteros_en_memoria():
    """El que lanza al lector se queda con el final de sus errores, no con
    todos: 300 MB de errores no pasan por su memoria."""
    r = subprocess.run([sys.executable, "-c", _ERRORES_LARGOS], capture_output=True, text=True,
                       cwd=_REPO, timeout=120,
                       env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(_REPO)})
    assert r.returncode == 0, r.stderr[-2000:]
    medido = json.loads(r.stdout)
    assert medido["error"].startswith("el lector de despachos salió con 1: "), medido["error"][:200]
    assert medido["error"].endswith("FIN DEL ERROR")
    assert medido["propio_mb"] < 100, medido["propio_mb"]


# --- Lo que encontró el adversario de la devolución -------------------------

@pytest.mark.parametrize("campo, rotulo, numero", [
    ("cant", "cantidad", "9" * 400),
    ("cant", "cantidad", "1.000.000.000.000,00"),
    ("unitario", "valor_unitario", "1.000.000.000.000,00"),
    ("kilo", "kilo_neto", "1000000000000,00"),  # sin puntos: la columna mide 18
], ids=["cantidad infinita", "cantidad en el tope", "unitario en el tope", "kilo en el tope"])
def test_un_numero_del_tope_para_arriba_queda_faltante_y_leer_no_da_500(
        auth_override, client, campo, rotulo, numero):
    """El lector usa el mismo tope que guardar: «9» × 400 era infinito y la
    respuesta, un 500."""
    texto = _item_solo(**{campo: numero})
    cid = _crear_cliente(client)
    r = _subir(client, cid, _pdf_con_texto(texto.splitlines()))
    assert r.status_code == 200, r.text
    renglon = r.json()["renglones"][0]
    assert renglon[rotulo] is None and rotulo in renglon["faltantes"]
    assert any("pasa del máximo" in a for a in renglon["avisos"]), renglon["avisos"]


def test_justo_debajo_del_tope_se_lee():
    from proyecto_maria.core.despacho_lector import leer_texto
    r = leer_texto(_item_solo(cant="999.999.999.999,00"))["renglones"][0]
    assert r["cantidad"] == 999999999999.0 and r["avisos"] == []


def test_un_caracter_suelto_que_no_es_unicode_avisa_y_leer_no_da_500(auth_override, client):
    """Una fuente que dice que «Z» es la mitad de un par (D800): escribir ese
    texto en UTF-8 fallaba en el lector y la respuesta era un 500."""
    texto = _item_solo().replace("COSA INVENTADA", "COSA Z INVENTADA")
    cid = _crear_cliente(client)
    r = _subir(client, cid, _pdf([[[(0, l)] for l in texto.splitlines()]], a_unicode={0x5A: "D800"}))
    assert r.status_code == 200, r.text
    renglon = r.json()["renglones"][0]
    assert renglon["descripcion"] == "COSA \ufffd INVENTADA"
    assert any("no se pudieron leer" in a for a in renglon["avisos"]), renglon["avisos"]


def test_el_lector_no_hereda_los_secretos_del_proceso(monkeypatch):
    import asyncio
    from proyecto_maria.core import despacho_lector
    monkeypatch.setenv("SECRET_KEY", "secreto-inventado")
    monkeypatch.setenv("DATABASE_URL", "postgresql://inventada")
    entornos = []
    real = asyncio.create_subprocess_exec

    async def mirar(*args, **kwargs):
        entornos.append(kwargs.get("env"))
        return await real(*args, **kwargs)

    monkeypatch.setattr(despacho_lector.asyncio, "create_subprocess_exec", mirar)
    r = asyncio.run(despacho_lector.leer_despacho_aparte(_despacho(), 60))
    assert r["renglones"], r
    assert entornos and set(entornos[0]) <= {"PATH", "HOME", "LANG", "LC_ALL", "PYTHONUSERBASE",
                                             "PYTHON_DOTENV_DISABLED"}
    # El lector de facturas carga el .env al importarse: el hijo no lo lee.
    assert entornos[0]["PYTHON_DOTENV_DISABLED"] == "1"


# --- DESPACHO-1b, devolución 20:07 -----------------------------------------

def test_un_pdf_que_da_mucho_trabajo_deja_de_leerse_por_tiempo_de_cpu():
    """20 hojas que comparten un contenido de 14 000 operaciones pesan 50 KB y
    costaban casi un segundo cada una: el tope de bytes no las frenaba."""
    from proyecto_maria.core.despacho_lector import leer_despacho
    from tests.pdf_bombas import trabajo
    leido = leer_despacho(trabajo(60), 0.5)
    [aviso] = [a for a in leido["avisos"] if a.startswith("El PDF da demasiado trabajo: leí hasta la hoja ")]
    assert int(aviso.rsplit(" ", 1)[1].rstrip(".")) < 60, aviso


def test_una_sola_hoja_cara_se_corta_en_el_tope_de_cpu():
    """Una hoja de 80 KB de «T*» cuesta unos 6 s: el tope se miraba sólo
    entre hojas y esa hoja se leía entera."""
    import time
    from proyecto_maria.core.despacho_lector import leer_despacho
    from tests.pdf_bombas import una_hoja_cara
    data = una_hoja_cara(80)
    antes = time.process_time()
    leido = leer_despacho(data, 0.5)
    gastado = time.process_time() - antes
    assert "El PDF da demasiado trabajo: leí hasta la hoja 0." in leido["avisos"], leido["avisos"]
    assert gastado < 2.5, gastado


def test_el_lector_aparte_corta_una_sola_hoja_cara():
    from proyecto_maria.core.despacho_lector import leer_despacho_aparte
    from tests.pdf_bombas import una_hoja_cara
    leido = asyncio.run(leer_despacho_aparte(una_hoja_cara(80), 120, limite_cpu_s=0.5))
    assert "El PDF da demasiado trabajo: leí hasta la hoja 0." in leido["avisos"], leido["avisos"]


def test_fuera_del_hilo_principal_el_tope_se_mira_entre_hojas():
    """Una señal sólo se atiende en el hilo principal: en otro hilo no hay
    temporizador y queda el control entre hojas."""
    import threading
    from proyecto_maria.core.despacho_lector import leer_despacho
    from tests.pdf_bombas import trabajo
    leido = {}
    hilo = threading.Thread(target=lambda: leido.update(leer_despacho(trabajo(60), 0.5)))
    hilo.start()
    hilo.join(120)
    assert not hilo.is_alive()
    [aviso] = [a for a in leido["avisos"] if a.startswith("El PDF da demasiado trabajo: leí hasta la hoja ")]
    assert int(aviso.rsplit(" ", 1)[1].rstrip(".")) < 60, aviso


def test_el_tope_de_cpu_deja_la_senal_como_estaba():
    import signal
    from proyecto_maria.core.despacho_lector import leer_despacho
    from tests.pdf_bombas import una_hoja_cara
    antes = signal.getsignal(signal.SIGPROF)
    leer_despacho(una_hoja_cara(80), 0.5)
    assert signal.getsignal(signal.SIGPROF) is antes
    assert signal.getitimer(signal.ITIMER_PROF) == (0.0, 0.0)


def test_el_lector_aparte_usa_el_tope_de_cpu_que_recibe():
    from proyecto_maria.core.despacho_lector import leer_despacho_aparte
    from tests.pdf_bombas import trabajo
    leido = asyncio.run(leer_despacho_aparte(trabajo(60), 120, limite_cpu_s=0.5))
    assert any(a.startswith("El PDF da demasiado trabajo") for a in leido["avisos"]), leido["avisos"]


def test_el_lector_aparte_tiene_tope_de_cpu_sin_pedirlo():
    """40 hojas de casi un segundo: sin tope, el lector seguía unos 40 s."""
    from proyecto_maria.core.despacho_lector import leer_despacho_aparte
    from tests.pdf_bombas import trabajo
    leido = asyncio.run(leer_despacho_aparte(trabajo(40), 120))
    assert any(a.startswith("El PDF da demasiado trabajo") for a in leido["avisos"]), leido["avisos"]


# El lector se reemplaza por uno falso: «cuenta» se anota en una carpeta y
# mira cuántos hay anotados a la vez; «espera» no termina hasta que aparece
# el archivo «soltar»; «rapido» contesta enseguida; «lista» contesta una
# lista; «sale5» sale con 5 sin leer lo que le mandan.
_HIJO_FALSO = r"""
import json, os, sys, time
carpeta, modo = sys.argv[1], sys.argv[2]
if modo == "cuenta":
    yo = os.path.join(carpeta, str(os.getpid()))
    open(yo, "w").close()
    vivos, fin = 0, time.monotonic() + 0.3
    while time.monotonic() < fin:
        vivos = max(vivos, len(os.listdir(carpeta)))
        time.sleep(0.01)
    os.remove(yo)
    print(json.dumps({"vivos": vivos}))
elif modo == "espera":
    hasta = time.monotonic() + 30
    while not os.path.exists(os.path.join(carpeta, "soltar")) and time.monotonic() < hasta:
        time.sleep(0.01)
    print(json.dumps({"renglones": []}))
elif modo == "rapido":
    print(json.dumps({"renglones": []}))
elif modo == "lista":
    print("[]")
elif modo == "sale5":
    sys.exit(5)
"""


def _lector_falso(monkeypatch, carpeta, modos):
    from proyecto_maria.core import despacho_lector
    real = asyncio.create_subprocess_exec

    async def falso(*args, **kwargs):
        return await real(sys.executable, "-c", _HIJO_FALSO, str(carpeta), modos.pop(0), **kwargs)

    monkeypatch.setattr(despacho_lector.asyncio, "create_subprocess_exec", falso)


def test_como_mucho_dos_lectores_a_la_vez(monkeypatch, tmp_path):
    from proyecto_maria.core.despacho_lector import leer_despacho_aparte
    _lector_falso(monkeypatch, tmp_path, ["cuenta"] * 5)

    async def cinco():
        return await asyncio.gather(*(leer_despacho_aparte(b"%PDF", 30, clave=f"usuario {n}")
                                      for n in range(5)))

    assert max(r["vivos"] for r in asyncio.run(cinco())) == 2


def test_un_usuario_lee_un_despacho_a_la_vez_y_no_frena_a_otro(monkeypatch, tmp_path):
    """Dos pedidos lentos del mismo usuario ocupaban los dos lugares y el de
    otro usuario esperaba hasta el tiempo máximo."""
    from proyecto_maria.core.despacho_lector import LectorOcupado, leer_despacho_aparte
    _lector_falso(monkeypatch, tmp_path, ["espera", "rapido", "rapido"])

    async def caso():
        lento = asyncio.create_task(leer_despacho_aparte(b"%PDF", 30, clave="usuario a"))
        await asyncio.sleep(0)  # que arranque y tome su lugar
        with pytest.raises(LectorOcupado):
            await leer_despacho_aparte(b"%PDF", 30, clave="usuario a")
        otro = await leer_despacho_aparte(b"%PDF", 30, clave="usuario b")
        (tmp_path / "soltar").touch()
        await lento
        # Al terminar, el mismo usuario puede leer otra vez.
        return otro, await leer_despacho_aparte(b"%PDF", 30, clave="usuario a")

    assert asyncio.run(caso()) == ({"renglones": []}, {"renglones": []})


def test_leer_con_otra_lectura_en_curso_da_429(auth_override, client, monkeypatch):
    from proyecto_maria.core import despacho_lector
    claves = []

    async def ocupado(data, limite_s, clave=None, **kwargs):
        claves.append(clave)
        raise despacho_lector.LectorOcupado(despacho_lector.AVISO_OCUPADO)

    monkeypatch.setattr(despacho_lector, "leer_despacho_aparte", ocupado)
    cid = _crear_cliente(client)
    r = _subir(client, cid)
    assert r.status_code == 429, r.text
    assert r.json() == {"detail": despacho_lector.AVISO_OCUPADO, "code": "lector_ocupado"}
    assert claves == [auth_override["username"]]


def test_un_lector_que_no_devuelve_un_objeto_es_un_error(monkeypatch, tmp_path):
    from proyecto_maria.core.despacho_lector import leer_despacho_aparte
    _lector_falso(monkeypatch, tmp_path, ["lista"])
    with pytest.raises(RuntimeError, match="no devolvió un resultado"):
        asyncio.run(leer_despacho_aparte(b"%PDF", 30))


def test_un_lector_que_sale_sin_leer_todo_dice_con_que_salio(monkeypatch, tmp_path):
    """8 MB no entran en el caño: escribir después de que el lector salió es
    un caño roto, y lo que importa es con qué salió."""
    from proyecto_maria.core.despacho_lector import leer_despacho_aparte
    _lector_falso(monkeypatch, tmp_path, ["sale5"])
    with pytest.raises(RuntimeError, match="salió con 5"):
        asyncio.run(leer_despacho_aparte(b"%PDF" + b"x" * (8 << 20), 30))


def test_sin_memoria_al_abrir_el_pdf_no_se_disfraza_de_pdf_roto(monkeypatch):
    """El proceso que lee sale con su código de «sin memoria» sólo si la
    MemoryError le llega."""
    import pypdf
    from proyecto_maria.core.despacho_lector import leer_despacho

    def sin_memoria(*args, **kwargs):
        raise MemoryError

    monkeypatch.setattr(pypdf, "PdfReader", sin_memoria)
    with pytest.raises(MemoryError):
        leer_despacho(b"%PDF")


@solo_linux
def test_una_hoja_que_se_infla_con_run_length_se_saltea():
    """Sin el tope de RunLength, pypdf deja inflar hasta 75 MB: con 70 MB el
    lector pasaba de 180 MB y el PDF entero se rechazaba."""
    medido = _medir_aparte("run_length", 70)
    assert "resultado" in medido, medido
    assert "No leí la hoja 1: es demasiado pesada." in medido["resultado"]["avisos"], medido
    assert medido["lector_mb"] < 100, medido


def test_los_topes_de_pypdf_cubren_todos_los_filtros(monkeypatch):
    """Todos los topes de salida de pypdf (de cada filtro) y los de largo y
    trabajo de un flujo, no sólo los de Flate."""
    import dataclasses

    import pypdf
    from pypdf._configuration import Configuration
    from proyecto_maria.core.despacho_lector import _MAX_FLUJO, texto_del_pdf
    pedidos = []
    real = pypdf.apply_configuration

    def mirar(**topes):
        pedidos.append(topes)
        return real(**topes)

    monkeypatch.setattr(pypdf, "apply_configuration", mirar)
    texto_del_pdf(_despacho())
    hacen_falta = {f.name for f in dataclasses.fields(Configuration)
                   if f.name.endswith("_maximum_output_length")}
    hacen_falta |= {"maximum_declared_stream_length", "stream_decoding_work_maximum_length"}
    assert len(pedidos) == 1 and {k for k, v in pedidos[0].items() if v == _MAX_FLUJO} >= hacen_falta, pedidos


def test_un_valor_a_la_izquierda_de_todos_los_rotulos_va_al_primero():
    from proyecto_maria.core.despacho_lector import _valores_por_columna
    assert _valores_por_columna("X", [(10, "A"), (30, "B")]) == {"A": "X"}


def test_el_tope_de_texto_de_verdad_corta_en_la_hoja_10():
    """Sin parchar el tope: 11 hojas de unos 400 000 caracteres."""
    from proyecto_maria.core.despacho_lector import texto_del_pdf
    from tests.pdf_bombas import texto_largo
    _, avisos = texto_del_pdf(texto_largo(11))
    assert avisos == ["El texto del PDF es demasiado largo: leí hasta la hoja 10."]


def test_guardar_justo_el_tope_de_renglones_se_guarda(auth_override, client):
    from proyecto_maria.core.despacho_lector import MAX_RENGLONES
    cid = _crear_cliente(client)
    r = _guardar(client, cid, [_renglon(f"TAPA INVENTADA {n}", "3926.90.90.000A")
                               for n in range(MAX_RENGLONES)])
    assert r.status_code == 200, r.text
    assert r.json()["guardados"] == MAX_RENGLONES


# Identidad: el mismo producto es el mismo NCM (sin mirar puntos) y la misma
# descripción entera.

def test_el_mismo_ncm_con_o_sin_puntos_es_el_mismo_producto(auth_override, client):
    cid = _crear_cliente(client)
    for posicion in ("8471.49.00", "84714900", "8471.4900"):
        assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", posicion)]).status_code == 200
    productos = _catalogo(client, cid)
    assert [(p["ncm"], p["veces_usado"]) for p in productos] == [("84714900", 3)], productos


def test_lo_aprendido_con_puntos_y_el_despacho_son_el_mismo_producto(auth_override, client):
    cid = _crear_cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "8471.49.00", "descripcion": "TAPA INVENTADA VERDE", "origen": "BR"}]})
    assert r.status_code == 200, r.text
    assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "8471.49.00.000A")]).status_code == 200
    productos = _catalogo(client, cid)
    assert [p["veces_usado"] for p in productos] == [2], productos


def test_dos_textos_largos_con_el_mismo_comienzo_no_se_funden(auth_override, client):
    """La descripción normalizada se corta en 200: dos renglones con los
    mismos 275 caracteres adelante quedaban en una fila con el peso mezclado."""
    cid = _crear_cliente(client)
    comienzo = ("MANUFACTURA INVENTADA DE PLASTICO " * 9)[:275]
    a, b = _renglon(comienzo + " TAPA", "3926.90.90.000A"), _renglon(comienzo + " CAJA", "3926.90.90.000A")
    b["kilo_neto"] = 500.0
    assert _guardar(client, cid, [a, b]).status_code == 200
    productos = _catalogo(client, cid)
    assert sorted((p["veces_usado"], p["peso_unitario_avg"]) for p in productos) == [
        (1, 0.1), (1, 50.0)], productos


# Promedios: cada uno cuenta sólo los usos que trajeron ese valor.

def test_el_promedio_no_cuenta_los_usos_sin_valor(auth_override, client):
    """Sin valor, después 2 kg y 3 de valor, después 4 kg y 6: da 3 y 4,5.
    Antes daba 2,67 y 4."""
    cid = _crear_cliente(client)
    for kilo, valor in ((None, None), (20.0, 3.0), (40.0, 6.0)):
        renglon = _renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")
        renglon.update(kilo_neto=kilo, valor_unitario=valor)
        assert _guardar(client, cid, [renglon]).status_code == 200
    [producto] = _catalogo(client, cid)
    assert (producto["veces_usado"], producto["peso_unitario_avg"], producto["valor_unitario_avg"]) == (
        3, 3.0, 4.5), producto


def test_el_historial_de_operaciones_tampoco_cuenta_los_usos_sin_valor(auth_override, client):
    from proyecto_maria.services.client_service import ClientService
    cid = _crear_cliente(client)
    base = {"ncm": "39269090", "descripcion": "TAPA INVENTADA VERDE"}
    for extra in ({}, {"peso_unitario": 2.0, "valor_unitario": 3.0, "cantidad": 10.0},
                  {"peso_unitario": 4.0, "valor_unitario": 6.0, "cantidad": 10.0}):
        asyncio.run(ClientService.update_product_history(cid, [{**base, **extra}]))

    async def fila():
        async with AsyncSessionLocal() as s:
            return (await s.execute(select(ClientProductHistory).where(
                ClientProductHistory.client_id == cid))).scalar_one()
    f = asyncio.run(fila())
    assert (f.veces_usado, f.peso_unitario_avg, f.valor_unitario_avg, f.cantidad_avg) == (3, 3.0, 4.5, 10.0)


# Topes: lo que no es un número de verdad no se guarda, y lo guardado antes
# no rompe el catálogo.

def test_aprender_un_peso_infinito_no_lo_guarda_y_el_catalogo_anda(auth_override, client):
    cid = _crear_cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "39269090", "descripcion": "TAPA INVENTADA VERDE", "peso_unitario": "inf",
         "valor_unitario": "inf"}]})
    assert r.status_code == 200, r.text
    [producto] = _catalogo(client, cid)
    assert (producto["peso_unitario_avg"], producto["valor_unitario_avg"]) == (0.0, None), producto


@pytest.mark.parametrize("campo", ["peso_unitario", "valor_unitario", "cantidad"])
def test_aprender_un_entero_enorme_no_da_500(auth_override, client, campo):
    """10**400 es JSON válido pero no entra en un float: daba 500. Va como
    cualquier valor que no es un número: ese producto no se aprende."""
    cid = _crear_cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "39269090", "descripcion": "TAPA INVENTADA VERDE", campo: 10 ** 400},
        {"ncm": "39269090", "descripcion": "TAPA INVENTADA AZUL", campo: 2}]})
    assert r.status_code == 200, r.text
    assert r.json()["aprendidos"] == 1
    assert [p["descripcion"] for p in _catalogo(client, cid)] == ["TAPA INVENTADA AZUL"]


def test_un_infinito_guardado_antes_no_rompe_el_catalogo_y_se_arregla(auth_override, client):
    cid = _crear_cliente(client)

    async def meter():
        async with AsyncSessionLocal() as s:
            s.add(ClientProductHistory(
                id=str(uuid.uuid4()), owner_username=auth_override["username"], client_id=cid,
                ncm="39269090", descripcion="TAPA INVENTADA VERDE",
                descripcion_normalizada="tapa inventada verde", peso_unitario_avg=float("inf"),
                origen_frecuente="BR", valor_unitario_avg=float("inf"), veces_usado=4))
            await s.commit()
    asyncio.run(meter())
    [producto] = _catalogo(client, cid)
    assert (producto["peso_unitario_avg"], producto["valor_unitario_avg"]) == (None, None), producto
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "39269090", "descripcion": "TAPA INVENTADA VERDE", "peso_unitario": 2,
         "valor_unitario": 3}]})
    assert r.status_code == 200, r.text
    [producto] = _catalogo(client, cid)
    assert (producto["peso_unitario_avg"], producto["valor_unitario_avg"]) == (2.0, 3.0), producto


def test_un_infinito_guardado_antes_no_rompe_la_busqueda(auth_override, client):
    """«/api/catalog/lookup» devuelve el valor recordado: un infinito viejo
    daba 500."""
    cid = _crear_cliente(client)

    async def meter():
        async with AsyncSessionLocal() as s:
            s.add(ClientProductHistory(
                id=str(uuid.uuid4()), owner_username=auth_override["username"], client_id=cid,
                ncm="39269090", descripcion="TAPA INVENTADA VERDE",
                descripcion_normalizada="tapa inventada verde", peso_unitario_avg=float("inf"),
                origen_frecuente="BR", valor_unitario_avg=float("inf"), veces_usado=4))
            await s.commit()
    asyncio.run(meter())
    r = client.post("/api/catalog/lookup", json={
        "items": [{"descripcion": "TAPA INVENTADA VERDE"}], "client_id": cid})
    assert r.status_code == 200, r.text
    [item] = r.json()["items"]
    assert (item["source"], item["ncm"], item["valor_unitario_avg"]) == ("cliente", "39269090", None), item


def test_aprender_con_puntos_suma_al_producto_del_despacho_y_no_a_otro(auth_override, client):
    """El despacho guarda «39269090»; aprender «3926.90.90» con la misma
    descripción no lo encontraba por NCM y el respaldo por descripción lo
    sumaba al primero parecido, que tenía otro NCM."""
    cid = _crear_cliente(client)
    assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "8471.30.12.000W"),
                                  _renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")]).status_code == 200
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "3926.90.90", "descripcion": "TAPA INVENTADA VERDE", "peso_unitario": 2}]})
    assert r.status_code == 200, r.text
    assert sorted((p["ncm"], p["veces_usado"]) for p in _catalogo(client, cid)) == [
        ("39269090", 2), ("84713012", 1)]


def test_el_peso_que_carga_la_persona_cuenta_como_un_uso(auth_override, client):
    """Tres despachos con peso y después la persona lo cambia a 2: el próximo
    de 4 da 3. Antes la corrección heredaba los tres usos y daba 2,5."""
    cid = _crear_cliente(client)
    for _ in range(3):
        assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")]).status_code == 200
    [producto] = _catalogo(client, cid)
    r = client.put(f"/api/clientes/{cid}/catalogo/productos/{producto['id']}",
                   json={"peso_unitario_avg": 2.0})
    assert r.status_code == 200, r.text
    renglon = _renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")
    renglon["kilo_neto"] = 40.0
    assert _guardar(client, cid, [renglon]).status_code == 200
    assert _catalogo(client, cid)[0]["peso_unitario_avg"] == 3.0


@pytest.mark.parametrize("peso", ["inf", "nan", -1, "1e400", 10 ** 400, "dos", False],
                         ids=["inf", "nan", "negativo", "1e400", "entero enorme", "dos", "false"])
def test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400(auth_override, client, peso):
    cid = _crear_cliente(client)
    assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")]).status_code == 200
    [producto] = _catalogo(client, cid)
    r = client.put(f"/api/clientes/{cid}/catalogo/productos/{producto['id']}",
                   json={"peso_unitario_avg": peso})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "El peso tiene que ser un número positivo."
    assert _catalogo(client, cid)[0]["peso_unitario_avg"] == 0.1


@pytest.mark.parametrize("cero", [0, "0", None, ""], ids=["cero", "cero en texto", "null", "vacio"])
def test_cambiar_el_peso_a_cero_lo_borra(auth_override, client, cero):
    cid = _crear_cliente(client)
    assert _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")]).status_code == 200
    [producto] = _catalogo(client, cid)
    r = client.put(f"/api/clientes/{cid}/catalogo/productos/{producto['id']}", json={"peso_unitario_avg": cero})
    assert r.status_code == 200, r.text
    assert _catalogo(client, cid)[0]["peso_unitario_avg"] == 0.0


def test_guardar_una_mitad_de_par_suelta_da_422(auth_override, client):
    """«\\ud800» es JSON válido pero no se puede escribir: daba 500."""
    cid = _crear_cliente(client)
    cuerpo = ('{"divisa": "USD", "renglones": [{"posicion_sim": "3926.90.90.000A", '
              '"descripcion": "TAPA \\ud800 INVENTADA", "origen": "BR"}]}')
    r = client.post(f"/api/clientes/{cid}/catalogo/despacho/guardar", content=cuerpo,
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 422, r.text
    assert r.json()["errores"] == [
        {"renglon": 1, "problemas": ["La descripción tiene un carácter que no se puede guardar."]}]
    assert _contar(ClientProductHistory, client_id=cid) == 0


@pytest.mark.parametrize("origen", ["\\ud800", "B\\ud800"], ids=["solo", "con una letra"])
def test_guardar_un_origen_con_mitad_de_par_da_422(auth_override, client, origen):
    """El 422 repetía el origen y no se podía mandar: daba 500."""
    cid = _crear_cliente(client)
    cuerpo = ('{"divisa": "USD", "renglones": [{"posicion_sim": "3926.90.90.000A", '
              '"descripcion": "TAPA INVENTADA", "origen": "%s"}]}' % origen)
    r = client.post(f"/api/clientes/{cid}/catalogo/despacho/guardar", content=cuerpo,
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 422, r.text
    assert r.json()["errores"] == [
        {"renglon": 1, "problemas": ["El origen tiene un carácter que no se puede guardar."]}]
    assert _contar(ClientProductHistory, client_id=cid) == 0


# D47: el catálogo guarda el valor unitario en dólares.

@pytest.mark.parametrize("divisa", ["EUR", None], ids=["en euros", "sin divisa"])
def test_guardar_un_despacho_que_no_esta_en_dolares_no_guarda_el_valor(auth_override, client, divisa):
    cid = _crear_cliente(client)
    r = _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")], divisa=divisa)
    assert r.status_code == 200, r.text
    assert r.json()["avisos"] == [
        {"renglon": 1, "aviso": "No guardé el valor unitario: el despacho no está en dólares."}]
    [producto] = _catalogo(client, cid)
    assert (producto["valor_unitario_avg"], producto["peso_unitario_avg"]) == (None, 0.1), producto


@pytest.mark.parametrize("divisa", ["USD", "DOL"])
def test_guardar_un_despacho_en_dolares_guarda_el_valor(auth_override, client, divisa):
    cid = _crear_cliente(client)
    r = _guardar(client, cid, [_renglon("TAPA INVENTADA VERDE", "3926.90.90.000A")], divisa=divisa)
    assert r.status_code == 200, r.text
    assert r.json()["avisos"] == []
    assert _catalogo(client, cid)[0]["valor_unitario_avg"] == 2.0
