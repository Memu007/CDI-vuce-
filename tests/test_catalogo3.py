"""CATALOGO-3: el catálogo distingue proveedores y productos sin letras latinas,
la memoria del cliente usa la misma clave, y el origen tiene un solo criterio
(nombre o código del país) en la factura, el catálogo y el agrupado.

El ancho de operation_items.origen en Postgres lo prueba
scripts/testing/catalogo3_postgres.py.
"""
import ast
import inspect
import os
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
             ("Proveedor sintetico", "钢管 2mm")]
    for vendor, desc in filas:
        assert _guardar(client, vendor, desc).status_code == 200
    viejo = {"TORNILLO": ("co_ltd", "tornillo"), "TUERCA": ("co_ltd", "tuerca"),
             "ARANDELA": ("", "arandela"), "电线 2mm": ("proveedor_sintetico", "2mm")}
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
    esperado = {d: (catalog_service._vendor_key(v), catalog_service.clave_de_producto(d)) for v, d in filas[:4]}
    esperado["SIN NOMBRE"] = ("~sin_nombre", "sin nombre")
    hechas = {d: (v, k) for v, k, d in primera if k != "2mm"}
    assert hechas == esperado
    assert [k for _, k, _ in primera if k == "2mm"] == ["2mm"], primera


@pytest.mark.parametrize("producto, empieza", [
    ({"descripcion": "TUERCA", "ncm": NCM, "origen": "XYZ"}, "Producto 2 («TUERCA»): "),
    ({"descripcion": 5, "ncm": NCM}, "Producto 2: "),
])
def test_el_error_del_catalogo_nombra_el_producto(client, producto, empieza):
    _cliente(client)
    r = client.post("/api/catalog/proveedor/productos", json={
        "vendor_name": VENDOR, "productos": [{"descripcion": "ARANDELA", "ncm": NCM}, producto]})
    assert r.status_code == 400 and r.json()["detail"].startswith(empieza), r.text


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
                          '"origen": "TAIWAN"}, {"descripcion": "Tuerca", "cantidad": 1, "origen": "XYZ"}]}')
    gemini = Mock()
    gemini.GenerativeModel.return_value.generate_content.return_value = respuesta
    with patch.object(pdf_extractor, "_load_gemini_client", return_value=gemini), \
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "ENABLE_FALLBACK_CASCADE": "false"}):
        items = pdf_extractor._llm_extract_pdf_items("Factura sintetica CATALOGO tres " + os.urandom(8).hex())
    assert [it["origen"] for it in items] == ["TAIWAN", "XX"]


def test_guardar_uso_con_un_origen_que_no_es_pais_da_400_y_no_suma(client):
    cid = _cliente(client)
    r = client.post("/api/ncm/guardar-uso", json={
        "descripcion": "TORNILLO", "ncm": NCM, "vendor_name": VENDOR, "origen": "XYZ", "client_id": cid})
    assert r.status_code == 400 and "XYZ" in r.json()["detail"], r.text
    assert _sql("select count(*) from ncm_historial where descripcion='TORNILLO' and ncm=:n", n=NCM)[0][0] == 0


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
