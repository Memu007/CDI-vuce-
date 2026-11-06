"""CATALOGO-LARGO-2: el catálogo del proveedor guarda entero el origen y el
nombre del proveedor, y guarda las descripciones sin letras latinas con una
clave propia que no se cruza con otra.

SQLite no controla el largo de las columnas: el corte de Postgres lo prueba
scripts/testing/catalogo_largo2_postgres.py.
"""
import pytest

from proyecto_maria.core.maria_generator import get_pais_codigo
from proyecto_maria.database.models import ClientProductHistory, VendorCatalogProduct
from tests.test_catalogo_largo1 import _dueno
from tests.test_guardar1 import _cliente, _sql
from tests.test_prelaunch_block2 import client  # noqa: F401

VENDOR_LARGO = "Proveedor sintetico " + "x" * 200
VENDOR_LARGO_ID = ("proveedor_sintetico_" + "x" * 200)[:60]
VENDOR = "Proveedor sintetico"
VENDOR_ID = "proveedor_sintetico"
NCM = "73181500"


def _match(client, vendor, descripcion):
    r = client.post("/api/catalog/match", json={"vendor_name": vendor, "items": [{"descripcion": descripcion}]})
    assert r.status_code == 200, r.text
    return r.json()["items_matched"][0]


def _filas(owner):
    return _sql("select vendor_nombre, descripcion, ncm, origen from vendor_catalog_products "
                "where owner_username=:o order by id", o=owner)


def test_el_origen_y_el_proveedor_no_tienen_tope_en_la_base():
    for tabla, columna in ((VendorCatalogProduct, "origen"), (VendorCatalogProduct, "vendor_nombre"),
                           (ClientProductHistory, "origen_frecuente")):
        assert tabla.__table__.c[columna].type.length is None, columna


@pytest.mark.parametrize("via", ["catalogo", "cambiar-origen", "guardar-uso", "guardar-uso-con-cliente"])
def test_el_origen_y_el_proveedor_se_guardan_enteros(client, via):
    cid = _cliente(client)
    owner = _dueno(cid)
    if via.startswith("guardar-uso"):
        r = client.post("/api/ncm/guardar-uso", json={
            "descripcion": "TORNILLO", "ncm": NCM, "vendor_name": VENDOR_LARGO, "origen": "TAIWAN",
            **({"client_id": cid} if via.endswith("cliente") else {})})
        assert r.json() == {"success": True, "historial_guardado": True}, r.text
    else:
        r = client.post(f"/api/catalog/{VENDOR_LARGO_ID}/productos", json={
            "vendor_name": VENDOR_LARGO,
            "productos": [{"descripcion": "TORNILLO", "ncm": NCM,
                           "origen": "CN" if via == "cambiar-origen" else "TAIWAN"}]})
        assert r.status_code == 200, r.text
    if via == "cambiar-origen":
        r = client.put(f"/api/catalog/{VENDOR_LARGO_ID}/productos/tornillo", json={"origen": "TAIWAN"})
        assert r.status_code == 200, r.text

    assert _filas(owner) == [(VENDOR_LARGO, "TORNILLO", NCM, "TAIWAN")]
    origen = _match(client, VENDOR_LARGO, "TORNILLO")["origen"]
    # El TXT busca el país por nombre: cortado a «TAI» saldría otro código.
    assert get_pais_codigo(origen) == 313 != get_pais_codigo("TAI")


# Descripciones sin letras latinas ni dígitos, cada una con su NCM. «ß» y «ﬁ»
# no son «ss» ni «fi»: son productos distintos.
SIN_LATINAS = [("螺丝", "73181500"), ("螺母", "73181600"), ("🔩", "85044090"),
               ("🔧", "84137010"), ("ß", "73182100"), ("ss", "73182200"),
               ("ﬁ", "73182300"), ("fi", "73182400")]


@pytest.mark.parametrize("via", ["catalogo", "guardar-uso"])
def test_lo_que_no_tiene_letras_latinas_se_guarda_sin_cruzarse(client, via):
    owner = _dueno(_cliente(client))
    if via == "catalogo":
        r = client.post(f"/api/catalog/{VENDOR_ID}/productos", json={
            "vendor_name": VENDOR, "productos": [{"descripcion": d, "ncm": n} for d, n in SIN_LATINAS]})
        assert r.status_code == 200 and r.json()["productos_nuevos"] == len(SIN_LATINAS), r.text
    else:
        for d, n in SIN_LATINAS:
            r = client.post("/api/ncm/guardar-uso", json={"descripcion": d, "ncm": n, "vendor_name": VENDOR})
            assert r.json() == {"success": True, "historial_guardado": True}, (d, r.text)

    assert sorted((d, n) for _, d, n, _ in _filas(owner)) == sorted(SIN_LATINAS)
    for d, n in SIN_LATINAS:
        m = _match(client, VENDOR, d)
        assert (m["match_type"], m["ncm"]) == ("exact", n), (d, m)


def test_cambiar_la_descripcion_a_una_sin_letras_latinas_mueve_la_clave(client):
    owner = _dueno(_cliente(client))
    url = f"/api/catalog/{VENDOR_ID}/productos"
    assert client.post(url, json={"vendor_name": VENDOR, "productos": [
        {"descripcion": "TORNILLO", "ncm": "73181500"}, {"descripcion": "螺母", "ncm": "73181600"}]}).status_code == 200

    r = client.put(f"{url}/tornillo", json={"descripcion_original": "螺丝"})
    clave = r.json()["producto"]["_key"]
    assert r.status_code == 200 and clave not in ("tornillo", ""), r.text
    # Otra igual a una que ya está choca, como con letras latinas.
    assert client.put(f"{url}/{clave}", json={"descripcion_original": "螺母"}).status_code == 404

    r = client.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": "TORNILLO", "ncm": "73182100"}]})
    assert r.status_code == 200 and r.json()["productos_nuevos"] == 1, r.text
    assert sorted((d, n) for _, d, n, _ in _filas(owner)) == [
        ("TORNILLO", "73182100"), ("螺丝", "73181500"), ("螺母", "73181600")]



@pytest.mark.parametrize("via, origenes", [
    ("guardar-uso", ["TAIWAN"]), ("aprender", ["JAPON"]), ("operacion", ["ALEMANIA"]),
    ("guardar-uso", ["CN", "TAIWAN"])], ids=["guardar-uso", "aprender", "operacion", "cambiar"])
def test_la_memoria_del_cliente_guarda_el_origen_entero(client, via, origenes):
    cid = _cliente(client)
    for origen in origenes:
        item = {"descripcion": "TORNILLO", "ncm": NCM, "origen": origen}
        if via == "guardar-uso":
            r = client.post("/api/ncm/guardar-uso", json={**item, "vendor_name": VENDOR, "client_id": cid})
            assert r.json() == {"success": True, "historial_guardado": True}, r.text
        else:
            url = f"/api/clientes/{cid}/" + ("catalogo/productos/learn" if via == "aprender" else "operaciones")
            assert client.post(url, json={"items": [item]}).status_code == 200

    assert _sql("select origen_frecuente from client_product_history where client_id=:c", c=cid) == [(origen,)]
    r = client.post("/api/catalog/lookup", json={"client_id": cid, "items": [{"descripcion": "TORNILLO"}]})
    sugerido = r.json()["items"][0]
    assert (sugerido["source"], sugerido["origen"]) == ("cliente", origen), sugerido
    assert get_pais_codigo(sugerido["origen"]) != get_pais_codigo(origen[:3])


GIGANTE = "x" * 2001


@pytest.mark.parametrize("via, campo", [
    ("catalogo", "proveedor"), ("catalogo", "origen"), ("cambiar-origen", "origen"),
    ("guardar-uso", "proveedor"), ("guardar-uso", "origen")])
def test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar(client, via, campo):
    owner = _dueno(_cliente(client))
    vendor = GIGANTE if campo == "proveedor" else VENDOR
    origen = GIGANTE if campo == "origen" else "CN"
    url = f"/api/catalog/{VENDOR_ID}/productos"
    if via == "cambiar-origen":
        assert client.post(url, json={"vendor_name": VENDOR, "productos": [
            {"descripcion": "TORNILLO", "ncm": NCM, "origen": "CN"}]}).status_code == 200
        r = client.put(f"{url}/tornillo", json={"origen": origen})
    elif via == "catalogo":
        r = client.post(url, json={"vendor_name": vendor, "productos": [
            {"descripcion": "TORNILLO", "ncm": NCM, "origen": origen}]})
    else:
        r = client.post("/api/ncm/guardar-uso", json={
            "descripcion": "TORNILLO", "ncm": NCM, "vendor_name": vendor, "origen": origen})

    motivo = {"proveedor": "El proveedor", "origen": "El origen"}[campo]
    assert (r.status_code, r.json().get("detail")) == (400, f"{motivo} pasa de 2000 caracteres."), r.text
    esperado = [(VENDOR, "TORNILLO", NCM, "CN")] if via == "cambiar-origen" else []
    assert _filas(owner) == esperado
    assert _sql("select count(*) from ncm_historial where owner_username=:o", o=owner) == [(0,)]


@pytest.mark.parametrize("via", ["aprender", "operacion"])
def test_la_memoria_del_cliente_no_guarda_un_origen_de_mas_de_2000(client, via):
    cid = _cliente(client)
    item = {"descripcion": "TORNILLO", "ncm": NCM, "origen": GIGANTE}
    url = f"/api/clientes/{cid}/" + ("catalogo/productos/learn" if via == "aprender" else "operaciones")
    r = client.post(url, json={"items": [item]})
    assert r.status_code == 200, r.text
    if via == "aprender":
        assert r.json()["aprendidos"] == 0, r.text
    else:
        assert r.json()["historial_guardado"] is False, r.text
    assert _sql("select count(*) from client_product_history where client_id=:c", c=cid) == [(0,)]


def test_una_fila_sin_descripcion_no_frena_el_lote_por_su_origen(client):
    owner = _dueno(_cliente(client))
    r = client.post(f"/api/catalog/{VENDOR_ID}/productos", json={"vendor_name": VENDOR, "productos": [
        {"descripcion": "", "ncm": NCM, "origen": GIGANTE}, {"descripcion": "TORNILLO", "ncm": NCM, "origen": "CN"}]})
    assert r.status_code == 200, r.text
    assert _filas(owner) == [(VENDOR, "TORNILLO", NCM, "CN")]
