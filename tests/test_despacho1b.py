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

def _pdf(paginas):
    """`paginas`: lista de hojas; cada hoja, lista de líneas; cada línea, lista
    de (columna, texto). Courier 9: cada columna mide 5,4 puntos."""
    objs = []

    def add(b):
        objs.append(b)
        return len(objs)

    fuente = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")
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


def _guardar(client, cid, renglones):
    return client.post(f"/api/clientes/{cid}/catalogo/despacho/guardar", json={"renglones": renglones})


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
    El lector se reemplaza por uno que no termina nunca."""
    real = asyncio.create_subprocess_exec
    procesos = []

    async def lector_colgado(*args, **kwargs):
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
