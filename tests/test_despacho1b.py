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
import uuid

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
