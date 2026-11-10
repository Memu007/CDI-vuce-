"""CATALOGO-3: el catálogo distingue proveedores y productos sin letras latinas,
la memoria del cliente usa la misma clave, y el origen tiene un solo criterio
(nombre o código del país) en la factura, el catálogo y el agrupado.

El ancho de operation_items.origen en Postgres lo prueba
scripts/testing/catalogo3_postgres.py.
"""
import ast
import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import unicodedata
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

import proyecto_maria.main as main
from proyecto_maria.core import catalog_service, maria_generator
from proyecto_maria.core.maria_generator import PAISES_INDEC, get_pais_codigo
from proyecto_maria.core.despacho_lector import origen_para_catalogo
from tests.test_catalogo_largo1 import _dueno
from tests.test_catalogo_largo2 import NCM, VENDOR, _escribir, _match
from tests.test_generar_maria_txt import _gen
from tests.test_guardar1 import SIM, _cliente, _sql
from tests.test_guardar1 import _guardar as _guardar_op
from tests.test_prelaunch_block2 import client  # noqa: F401

LARGO = "Proveedor sintetico " + "x" * 60


def _guardar(client, vendor, desc, ncm=NCM, **extra):
    return client.post("/api/catalog/proveedor/productos", json={
        "vendor_name": vendor, "productos": [{"descripcion": desc, "ncm": ncm, **extra}]})


def _ids(owner):
    return _sql("select vendor_id, product_key, descripcion from vendor_catalog_products "
                "where owner_username=:o order by id", o=owner)


@pytest.mark.parametrize("a, b", [
    ("深圳甲", "广州乙"),
    ("深圳甲有限公司 Co., Ltd", "广州乙有限公司 Co., Ltd"),
    ("🔩", "🔧"),
    (LARGO + "A", LARGO + "B"),
], ids=["cjk", "cjk-co-ltd", "emoji", "prefijo-60"])
def test_dos_proveedores_distintos_no_comparten_catalogo(client, a, b):
    _cliente(client)
    ra = _guardar(client, a, "TORNILLO")
    assert ra.status_code == 200, ra.text
    m = _match(client, b, "TORNILLO")
    assert m["match_type"] == "none", m
    assert _match(client, a, "TORNILLO")["match_type"] == "exact"
    rb = _guardar(client, b, "TUERCA")
    assert rb.status_code == 200, rb.text
    ida, idb = ra.json()["vendor_id"], rb.json()["vendor_id"]
    assert ida != idb and catalog_service.is_valid_vendor_id(ida) and catalog_service.is_valid_vendor_id(idb)
    for vid, desc in ((ida, "TORNILLO"), (idb, "TUERCA")):
        r = client.get(f"/api/catalog/{vid}")
        assert r.status_code == 200, r.text
        assert [p["descripcion_original"] for p in r.json()["productos"].values()] == [desc], r.text


@pytest.mark.parametrize("nombre, vid", [
    ("Proveedor sintetico", "proveedor_sintetico"),
    ("  Acme   Corp, S.A. ", "acme_corp_s_a"),
    ("Ñandú Hnos.", "nandu_hnos"),
    ("Shenzhen Co., Ltd", "shenzhen_co_ltd"),
    ("Industrias García Nº1", "industrias_garcia_n_1"),
    ("Hermanos 1ª SA", "hermanos_1_sa"),
    ("10µF Corp", "10_f_corp"),
])
def test_un_proveedor_latino_conserva_su_id(nombre, vid):
    assert catalog_service._vendor_key(nombre) == vid


@pytest.mark.parametrize("vendor", ["", "\x00", "  \x00 "])
def test_sin_nombre_de_proveedor_no_guarda_ni_encuentra(client, vendor):
    owner = _dueno(_cliente(client))
    _guardar(client, "Otro", "TORNILLO")
    _escribir("update vendor_catalog_products set vendor_id='' where owner_username=:o", o=owner)
    r = _guardar(client, vendor, "TUERCA")
    assert r.status_code == 400, r.text
    assert [d for _, _, d in _ids(owner)] == ["TORNILLO"]
    if vendor:
        assert _match(client, vendor, "TORNILLO")["match_type"] == "none"


@pytest.mark.parametrize("a, b", [("电线 2mm", "钢管 2mm"), ("螺丝 M8x20", "螺母 M8x20")])
def test_productos_sin_letras_latinas_con_la_misma_medida_no_se_pisan(client, a, b):
    owner = _dueno(_cliente(client))
    assert _guardar(client, VENDOR, a, ncm=NCM).status_code == 200
    assert _guardar(client, VENDOR, b, ncm="84714900").status_code == 200
    assert sorted(d for _, _, d in _ids(owner)) == sorted([a, b])
    assert (_match(client, VENDOR, a)["ncm"], _match(client, VENDOR, b)["ncm"]) == (NCM, "84714900")
    otro = _match(client, VENDOR, b + " 新")
    assert otro["ncm"] != NCM, otro


def test_la_memoria_del_cliente_usa_la_misma_clave(client):
    cid = _cliente(client)
    r = client.post("/api/ncm/guardar-uso", json={
        "descripcion": "电线 2mm", "ncm": NCM, "vendor_name": VENDOR, "client_id": cid})
    assert r.json() == {"success": True, "historial_guardado": True}, r.text

    def _lookup(desc):
        r = client.post("/api/catalog/lookup", json={
            "items": [{"descripcion": desc}], "vendor_name": VENDOR, "client_id": cid})
        assert r.status_code == 200, r.text
        return r.json()["items"][0]
    assert (_lookup("电线 2mm")["source"], _lookup("电线 2mm")["ncm"]) == ("cliente", NCM)
    otro = _lookup("钢管 2mm")
    assert (otro["source"], otro["ncm"]) == ("ninguno", None), otro


@pytest.mark.parametrize("guardado, buscado, como", [
    ("Capacitor 10µF 50V", "Capacitor 10μF 50V", "exact"),
    ("Capacitor 10μF 50V", "Capacitor 10µF 50V", "exact"),
    ("Bolt ｶﾞｽ M8", "Bolt ガス M8", "exact"),
    ("Bolt ガス M8", "Bolt ｶﾞｽ M8", "exact"),
    ("Cable 2,5mm²", "Cable 2,5mm2", "exact"),
    ("Arandela ﬁna", "Arandela fina", "exact"),
    ("Tornillo Nº 8", "Tornillo N° 8", "exact"),
    ("Bolt™ M8", "Bolt M8", "exact"),
    ("Screw M8", "Screw M8 螺丝", "fuzzy"),
    ("Screw M8 螺丝", "Screw M8", "fuzzy"),
    ("电线 2mm", "钢管 2mm", "none"),
])
def test_lo_que_se_lee_igual_se_encuentra(client, guardado, buscado, como):
    cid = _cliente(client)
    r = client.post("/api/ncm/guardar-uso", json={
        "descripcion": guardado, "ncm": NCM, "vendor_name": VENDOR, "client_id": cid})
    assert r.json() == {"success": True, "historial_guardado": True}, r.text
    m = _match(client, VENDOR, buscado)
    assert (m["match_type"], m["match_score"] == 1.0) == (como, como == "exact"), m
    r = client.post("/api/catalog/lookup", json={
        "items": [{"descripcion": buscado}], "vendor_name": "Otro", "client_id": cid})
    mem = r.json()["items"][0]
    assert (mem["source"], mem["confidence"] == 1.0) == (
        "ninguno" if como == "none" else "cliente", como == "exact"), mem


@pytest.mark.parametrize("recordado, del_proveedor, sale", [
    ("螺丝钉", "螺丝钉", SIM),
    ("电线 2mm", "钢管 2mm", "84714900"),
])
def test_el_ncm_recordado_compara_con_la_clave_del_catalogo(recordado, del_proveedor, sale):
    mem = {"ncm": "84714900", "descripcion": recordado}
    vm = {"producto_key": catalog_service.clave_de_producto(del_proveedor), "ncm": SIM}
    assert main._ncm_recordado_con_sim_del_proveedor(mem, vm) == sale


def _migrar():
    with TestClient(main.app):
        pass


def test_la_migracion_separa_los_proveedores_y_los_productos_mezclados(client):
    owner = _dueno(_cliente(client))
    filas = [("深圳甲有限公司 Co., Ltd", "TORNILLO"), ("广州乙有限公司 Co., Ltd", "TUERCA"),
             ("深圳甲", "ARANDELA"), ("Proveedor sintetico", "电线 2mm"),
             ("Proveedor sintetico", "螺丝 3mm"), ("Proveedor sintetico", "钢管 2mm")]
    for vendor, desc in filas:
        assert _guardar(client, vendor, desc).status_code == 200
    viejo = {"TORNILLO": ("co_ltd", "tornillo"), "TUERCA": ("co_ltd", "tuerca"),
             "ARANDELA": ("", "arandela"), "电线 2mm": ("proveedor_sintetico", "2mm"),
             "螺丝 3mm": ("proveedor_sintetico", "3mm")}
    for desc, (vid, key) in viejo.items():
        _escribir("update vendor_catalog_products set vendor_id=:v, product_key=:k "
                  "where owner_username=:o and descripcion=:d", v=vid, k=key, o=owner, d=desc)
    _guardar(client, "Otro", "SIN NOMBRE")
    _escribir("update vendor_catalog_products set vendor_id='', vendor_nombre=null "
              "where owner_username=:o and descripcion='SIN NOMBRE'", o=owner)
    # El destino de «电线 2mm» ya está ocupado: esa fila vieja choca y queda con su clave.
    _escribir("update vendor_catalog_products set product_key=:k, descripcion='电线 2mm' "
              "where owner_username=:o and descripcion='钢管 2mm'",
              k=catalog_service.clave_de_producto("电线 2mm"), o=owner)
    _migrar()
    primera = _ids(owner)
    _migrar()
    assert _ids(owner) == primera
    esperado = {d: (catalog_service._vendor_key(v), catalog_service.clave_de_producto(d)) for v, d in filas[:-1]}
    esperado["SIN NOMBRE"] = ("~sin_nombre", "sin nombre")
    hechas = {d: (v, k) for v, k, d in primera if k != "2mm"}
    assert hechas == esperado
    assert [k for _, k, _ in primera if k == "2mm"] == ["2mm"], primera


def test_la_tabla_de_paises_no_tiene_claves_repetidas_salvo_nl():
    fuente = inspect.getsource(maria_generator)
    arbol = ast.parse(fuente)
    literal = next(n.value for n in ast.walk(arbol) if isinstance(n, ast.Assign)
                   and any(getattr(t, "id", None) == "PAISES_INDEC" for t in n.targets))
    claves = [k.value for k in literal.keys]
    assert {k for k in claves if claves.count(k) > 1} == {"NL"}


def test_nombre_y_codigo_de_cada_pais_dan_el_mismo_codigo():
    for nombre, codigo in PAISES_INDEC.items():
        guardado, problema = origen_para_catalogo(nombre)
        assert problema is None and get_pais_codigo(guardado) == codigo, (nombre, guardado, problema)
    assert [get_pais_codigo(origen_para_catalogo(p)[0]) for p in ("PAISES BAJOS", "HOLANDA", "NL")] == [423, 434, 434]
    # «123» es LIBIA en la tabla oficial: un código de la tabla vale como «310».
    assert [origen_para_catalogo(c)[0] for c in ("123", "310")] == ["123", "310"]
    for malo in ("XYZ", "ZZ", "99999", "ＢＲ", "ÉS"):
        assert origen_para_catalogo(malo)[0] is None, malo


def test_el_extractor_conserva_el_nombre_del_pais():
    from proyecto_maria import pdf_extractor
    respuesta = Mock(text='{"items": [{"descripcion": "Tornillo", "cantidad": 1, "valor_unitario": 1, '
                          '"origen": "TAIWAN"}, {"descripcion": "Tuerca", "cantidad": 1, "origen": "XYZ"}, '
                          '{"descripcion": "Perno", "cantidad": 1, "origen": "123"}, '
                          '{"descripcion": "Clavo", "cantidad": 1, "origen": "Alemania Federal"}]}')
    gemini = Mock()
    gemini.GenerativeModel.return_value.generate_content.return_value = respuesta
    with patch.object(pdf_extractor, "_load_gemini_client", return_value=gemini), \
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "ENABLE_FALLBACK_CASCADE": "false"}):
        items = pdf_extractor._llm_extract_pdf_items("Factura sintetica CATALOGO tres " + os.urandom(8).hex())
    assert [it["origen"] for it in items] == ["TAIWAN", "XX", "123", "Alemania Federal"]
    # El lector de la factura con cabecera pasa a dos letras lo que tiene ISO; «123» es LIBIA.
    assert [pdf_extractor._origen_desde_factura(o) for o in ("123", "Alemania Federal", "XYZ")] == [
        "LY", "Alemania Federal", ""]


# Reconocidos con su código MARIA; los demás se guardan sin origen y avisan.
FAMILIA_ORIGEN = {"CHN": 310, "ITA": 417, "Hong Kong": 341, "MACAO": 344, "Viet Nam": None,
                  "U.S.A.": None, "PRC": None, "Turkey": None, "TAI": None}


@pytest.mark.parametrize("origen", FAMILIA_ORIGEN)
def test_guardar_uso_no_pierde_el_ncm_por_un_origen_que_no_reconoce(client, origen):
    cid = _cliente(client)
    owner, desc = _dueno(cid), f"TORNILLO {origen}"
    r = client.post("/api/ncm/guardar-uso", json={
        "descripcion": desc, "ncm": NCM, "vendor_name": VENDOR, "origen": origen, "client_id": cid})
    assert r.status_code == 200 and r.json()["historial_guardado"] is True, r.text
    assert _sql("select ncm from ncm_historial where owner_username=:o and descripcion=:d",
                o=owner, d=desc) == [(NCM,)]
    (hist,), (cat,) = (_sql("select origen_frecuente from client_product_history where client_id=:c", c=cid),
                       _sql("select origen from vendor_catalog_products where owner_username=:o", o=owner))
    codigo = FAMILIA_ORIGEN[origen]
    if codigo is None:
        assert origen in r.json()["aviso"] and cat == (None,) and hist[0] in (None, "XX"), (r.text, hist, cat)
    else:
        assert "aviso" not in r.json() and get_pais_codigo(cat[0]) == codigo == get_pais_codigo(hist[0]), (hist, cat)


def test_el_error_del_catalogo_nombra_el_producto(client):
    _cliente(client)
    r = client.post("/api/catalog/proveedor/productos", json={
        "vendor_name": VENDOR, "productos": [{"descripcion": "ARANDELA", "ncm": NCM}, {"descripcion": 5, "ncm": NCM}]})
    assert r.status_code == 400 and r.json()["detail"].startswith("Producto 2: "), r.text


@pytest.mark.parametrize("origen", FAMILIA_ORIGEN)
def test_un_origen_que_no_reconoce_no_hace_perder_el_lote(client, origen):
    owner = _dueno(_cliente(client))
    r = client.post("/api/catalog/proveedor/productos", json={"vendor_name": VENDOR, "productos": [
        {"descripcion": "ARANDELA", "ncm": NCM}, {"descripcion": "TUERCA", "ncm": NCM, "origen": origen}]})
    assert r.status_code == 200, r.text
    filas = _sql("select descripcion, ncm, origen from vendor_catalog_products where owner_username=:o "
                 "order by descripcion", o=owner)
    if FAMILIA_ORIGEN[origen] is None:
        assert r.json()["avisos"] == [f"Producto 2 («TUERCA»): No reconozco el origen «{origen}»: "
                                      "usá el nombre o el código del país."], r.text
        assert filas == [("ARANDELA", NCM, None), ("TUERCA", NCM, None)]
    else:
        assert r.json()["avisos"] == [] and get_pais_codigo(filas[1][2]) == FAMILIA_ORIGEN[origen], (r.text, filas)


# Forma escrita → código MARIA, o None si no se reconoce (el TXT cae en el default de cada régimen).
LECTURA_PAIS = {"CHINA\xa0": 310, "HONG\u2009KONG": 341, "\u3000CHINA": 310, "ＣＨＩＮＡ": 310, "CHINA\n": 310,
                "310 - CHINA": 310, "203 - BRASIL": 203, "435 · CHIPRE": 435, "436 · TURQUIA": 436,
                "123": 123, "Alemania Federal": 402, "310 - Vietnam": None, "203-ARG": None,
                "435 · TURQUIA": None, "\n": None, "XYZ": None, "1" * 5000: None}


@pytest.mark.parametrize("escrito", LECTURA_PAIS, ids=lambda e: e[:20])
def test_cada_forma_del_pais_da_el_mismo_codigo_al_importar_y_exportar(escrito):
    from proyecto_maria.core import maria_generator_export
    codigo = LECTURA_PAIS[escrito]
    assert maria_generator.codigo_de_pais(escrito) == codigo
    guardado = maria_generator.origen_valido(escrito)
    assert (guardado is None) == (codigo is None)
    assert guardado is None or guardado == " ".join(guardado.split()), repr(guardado)
    importa, exporta = get_pais_codigo(escrito), maria_generator_export.get_pais_codigo(escrito)
    if codigo is None:
        assert (importa, exporta) == (maria_generator.PAIS_DEFAULT_IMPORT, maria_generator_export.PAIS_DEFAULT_EXPORT)
    else:
        assert importa == exporta == codigo


@pytest.mark.parametrize("origen", ["TAI", "PRC"])
def test_cambiar_el_ncm_de_una_fila_con_origen_viejo_guarda_el_ncm(client, origen):
    owner = _dueno(_cliente(client))
    vid = _guardar(client, VENDOR, "TUERCA").json()["vendor_id"]
    _escribir("update vendor_catalog_products set origen=:x where owner_username=:o", x=origen, o=owner)
    (key,) = [k for (_, k, _) in _ids(owner)]
    r = client.put(f"/api/catalog/{vid}/productos/{key}", json={"ncm": "84714900", "origen": origen})
    assert r.status_code == 200 and origen in r.json()["aviso"], r.text
    assert _sql("select ncm, origen from vendor_catalog_products where owner_username=:o", o=owner) == [
        ("84714900", origen)]


# Pedazos de nombres de zonas francas y territorios («ZF CORDOBA»): no son un país.
NO_SON_PAISES = ("AFRICA", "AMERICA", "OCEANIA", "ISLAS", "(AAE)", "ESTADO ASOCIADO", "BUENOS AIRES", "CORDOBA")


# Python y JavaScript no recortan los mismos espacios; «𝐁𝐑» son dos letras y cuatro unidades UTF-16.
ESPACIOS_RAROS = ["𝐁𝐑", "\ufeffCHINA", "CHINA\ufeff", "CHINA\x85", "\x1cBR", "ARABIA\x1fSAUDITA",
                  "302\u2028·\u2028ARABIA\u2028SAUDITA"]


def _resolve_de_la_pantalla(valores):
    js = maria_generator._PAISES_PANTALLA
    codigo = (f"global.window = {{}}; require({str(js)!r}); const v = JSON.parse(require('fs')"
              ".readFileSync(0, 'utf8')); console.log(JSON.stringify(v.map(window.CDI.paisesMaria.resolve)));")
    return json.loads(subprocess.run(["node", "-e", codigo], input=json.dumps(valores), check=True,
                                     capture_output=True, text=True).stdout)


@pytest.mark.skipif(not shutil.which("node"), reason="sin node")
def test_la_pantalla_y_el_servidor_reconocen_los_mismos_paises():
    from proyecto_maria.core.paises_iso3 import ISO3_A_ISO2
    codigos = sorted(maria_generator.codigos_tabla_oficial())
    valores = [*FAMILIA_ORIGEN, *PAISES_INDEC, *ISO3_A_ISO2, *(f"0{c}" for c in codigos),
               *(f"{c} · X" for c in codigos), "0313", "123", "ÉS", "ＢＲ", "XYZ", "99999", "Türkiye", "",
               *ESPACIOS_RAROS,
               *LECTURA_PAIS, *NO_SON_PAISES]
    servidor = [str(maria_generator.codigo_de_pais(v) or "") for v in valores]
    distintos = [(v, p, s) for v, p, s in zip(valores, _resolve_de_la_pantalla(valores), servidor) if p != s]
    assert distintos == []
    assert [s for v, s in zip(valores, servidor) if v in NO_SON_PAISES] == [""] * len(NO_SON_PAISES)


def test_el_txt_usa_el_codigo_de_cada_forma_reconocida():
    items = [{"pieza": "84713000", "descripcion": f"Producto {o}", "cantidad": 1, "valor_unitario": 10,
              "peso_unitario": 1, "origen": o, "unidad": "07", "grupo_id": i}
             for i, o in enumerate(["Hong Kong", "CHN", "ITA", "313 · TAIWAN"], start=1)]
    txt = _gen("OP123456", items)
    assert re.findall(r"CARTPAYORI=(\d+)", txt) == ["341", "310", "417", "313"]


ORIGENES = ("313", "TAIWAN", "TW")


def test_el_txt_agrupa_el_mismo_pais_escrito_de_tres_formas():
    items = [{"pieza": "84713000", "descripcion": f"Producto {o}", "cantidad": 1, "valor_unitario": 10,
              "peso_unitario": 1, "origen": o, "unidad": "07", "grupo_id": 1} for o in ORIGENES]
    txt = _gen("OP123456", items)
    assert "CARTPAYORI=313" in txt


def test_agrupar_por_la_api_acepta_el_mismo_pais_escrito_de_tres_formas(client):
    cid = _cliente(client)
    r = _guardar_op(client, cid, [{"descripcion": f"P {o}", "ncm": "84714900", "origen": o, "cantidad": 1}
                                  for o in ORIGENES])
    assert r.status_code == 200, r.text
    op = r.json()["operation_id"]
    ids = [i for (i,) in _sql("select id from operation_items where operation_id=:o", o=op)]
    r = client.post(f"/api/operacion/{op}/agrupar", json={"item_ids": ids})
    assert r.status_code == 200, r.text
    assert sorted(o for (o,) in _sql("select origen from operation_items where operation_id=:o", o=op)) == sorted(ORIGENES)


def test_el_origen_frecuente_cuenta_el_pais_y_no_la_forma(client):
    cid = _cliente(client)
    origenes = ["CN"] * 3 + ["CHINA"] * 2 + ["US"] * 4
    r = _guardar_op(client, cid, [{"descripcion": f"P{i}", "ncm": "84714900", "origen": o, "cantidad": 1}
                                  for i, o in enumerate(origenes)])
    assert r.status_code == 200, r.text
    r = client.get(f"/api/clientes/{cid}/metricas")
    assert r.status_code == 200 and r.json()["origen_frecuente"] == "CN", r.text


@pytest.mark.parametrize("origen, avisa", [("TAIWAN", False), ("TW", False), ("313", False), ("XYZ", True)])
def test_el_estimador_de_tarifar_reconoce_el_pais_igual_que_el_catalogo(origen, avisa):
    from proyecto_maria.core.tarifar_connector import CLIENT
    r = CLIENT._calcular_item_individual({"ncm": NCM, "descripcion": "Tornillo", "cantidad": 1,
                                          "valor_unitario": 1, "peso_unitario": 1, "origen": origen})
    assert any("no reconocido" in w for w in r.warnings) is avisa, r.warnings


def test_un_origen_de_miles_de_cifras_no_rompe_los_avisos_ni_el_txt(client):
    from tests.test_maria7_rechazos_24_10 import LONA, _registrar_con_cuit
    from tests.test_valor1 import _pedido_con
    _registrar_con_cuit(client, "catalogo3_cifras")
    pedido = _pedido_con([LONA])
    pedido["items"][0]["origen"] = "1" * 5000
    r = client.post("/generate_maria/avisos", json=pedido)
    assert r.status_code == 200, r.text[:300]
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400 and "Origen no reconocido" in r.text, r.text[:300]


@pytest.mark.parametrize("escenario", ["confirmar-ncm", "asignar-ncm"])
def test_la_pantalla_avisa_que_se_guardo_sin_origen(escenario):
    from tests.test_despacho1c import pantalla

    aviso = "Se guardó sin origen. Origen sintético no reconocido."
    vista = pantalla(escenario, {"success": True, "historial_guardado": True, "aviso": aviso})
    assert vista["toasts"] and vista["toasts"][-1]["tipo"] == "warning", vista
    assert vista["toasts"][-1]["detalle"] == aviso, vista


def _normalize_lento(text):
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _sufijo_lento(texto):
    fuera = "".join(
        c for c in unicodedata.normalize("NFC", texto)
        if unicodedata.category(c)[0] == "L" or unicodedata.category(c) == "Nd"
        if not _normalize_lento(c) and c > "ɏ" and not unicodedata.name(c, "").startswith("LATIN")
    )
    return hashlib.sha256(fuera.casefold().encode("utf-8", "surrogatepass")).hexdigest()[:16] if fuera else ""


def _compatible_lento(texto):
    return unicodedata.normalize("NFC", "".join(
        c if c in "ºª" or unicodedata.category(c)[0] == "S" else unicodedata.normalize("NFKC", c)
        for c in texto))


def test_acelerar_no_cambia_ninguna_clave():
    textos = ["", " ", "TORNILLO M8 x 20", "Tornillo  m8\tx20", "Ñandú ÉSPÁRRAGO çà", "Nº1 ª º µ ß ÿ",
              "螺丝 M8", "电线", "Ｂｏｌｔ １２", "ｶﾞｽ", "🔩 bolt", "Bolt™ ©", "ǅ ǈ Ⅻ ①", "Ωmega Σ", "ɐ ʼn",
              "á̧", "\ud800x", "x" * 2000, "Tornillo acero inoxidable " * 20, "螺丝" * 300]
    for t in textos:
        assert catalog_service._normalize(t) == _normalize_lento(t), t
        assert catalog_service._sufijo(t) == _sufijo_lento(t), t
        assert catalog_service._compatible(t) == _compatible_lento(t), t
