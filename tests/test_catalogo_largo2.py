"""CATALOGO-LARGO-2: el catálogo del proveedor guarda entero el origen y el
nombre del proveedor, y guarda las descripciones sin letras latinas con una
clave propia que no se cruza con otra.

SQLite no controla el largo de las columnas: el corte de Postgres lo prueba
scripts/testing/catalogo_largo2_postgres.py.
"""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import proyecto_maria.main as main

from proyecto_maria.core.maria_generator import get_pais_codigo
from proyecto_maria.core import catalog_service
from proyecto_maria.database.models import ClientProductHistory, VendorCatalogProduct
from tests.test_catalogo_largo1 import _dueno
from tests.test_guardar1 import _cliente, _sql
from tests.test_prelaunch_block2 import client  # noqa: F401

VENDOR_LARGO = "Proveedor sintetico " + "x" * 200
VENDOR_LARGO_ID = catalog_service._vendor_key(VENDOR_LARGO)
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


def test_los_topes_del_catalogo_en_la_base():
    for tabla, columna in ((VendorCatalogProduct, "origen"), (VendorCatalogProduct, "vendor_nombre"),
                           (ClientProductHistory, "origen_frecuente")):
        assert tabla.__table__.c[columna].type.length is None, columna
    assert VendorCatalogProduct.__table__.c["ncm"].type.length == catalog_service.MAX_NCM


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
NCM_LARGO = "7" * 21
DE_MAS = {"proveedor": ("El proveedor pasa de 2000 caracteres.", "El proveedor pasa de 2000 caracteres."),
          "origen": ("El origen pasa de 2000 caracteres.", "El origen pasa de 2000 caracteres."),
          "ncm": ("El NCM pasa de 20 caracteres.", "La NCM pasa de 20 caracteres.")}


@pytest.mark.parametrize("via, campo", [
    ("catalogo", "proveedor"), ("catalogo", "origen"), ("catalogo", "ncm"),
    ("cambiar", "origen"), ("cambiar", "ncm"),
    ("guardar-uso", "proveedor"), ("guardar-uso", "origen"), ("guardar-uso", "ncm")])
def test_un_texto_de_mas_da_400_sin_guardar(client, via, campo):
    owner = _dueno(_cliente(client))
    vendor = GIGANTE if campo == "proveedor" else VENDOR
    origen = GIGANTE if campo == "origen" else "CN"
    ncm = NCM_LARGO if campo == "ncm" else NCM
    url = f"/api/catalog/{VENDOR_ID}/productos"
    if via == "cambiar":
        assert client.post(url, json={"vendor_name": VENDOR, "productos": [
            {"descripcion": "TORNILLO", "ncm": NCM, "origen": "CN"}]}).status_code == 200
        r = client.put(f"{url}/tornillo", json={campo: {"origen": origen, "ncm": ncm}[campo]})
    elif via == "catalogo":
        r = client.post(url, json={"vendor_name": vendor, "productos": [
            {"descripcion": "TORNILLO", "ncm": ncm, "origen": origen}]})
    else:
        r = client.post("/api/ncm/guardar-uso", json={
            "descripcion": "TORNILLO", "ncm": ncm, "vendor_name": vendor, "origen": origen})

    motivo = DE_MAS[campo][via == "guardar-uso"]
    if via == "catalogo" and campo != "proveedor":
        motivo = "Producto 1 («TORNILLO»): " + motivo
    assert (r.status_code, r.json().get("detail")) == (400, motivo), r.text
    esperado = [(VENDOR, "TORNILLO", NCM, "CN")] if via == "cambiar" else []
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


# Un valor bueno por campo y lo que se le hace para volverlo malo.
BUENOS = {"proveedor": VENDOR, "descripción": "TUERCA", "origen": "TAIWAN", "ncm": "73181600"}
QUE = {"proveedor": "El proveedor", "descripción": "La descripción", "origen": "El origen", "ncm": "El NCM"}
MALOS = {"nulo": lambda b: b[:4] + "\x00" + b[4:], "medio par": lambda b: b + "\ud800",
         "false": lambda b: False, "lista": lambda b: [], "null": lambda b: None}
CLAVES = {"proveedor": "vendor_name", "descripción": "descripcion", "origen": "origen", "ncm": "ncm"}


def _mandar(client, metodo, ruta, cuerpo):
    # Con ensure_ascii el medio par viaja escapado, como en un JSON de verdad.
    return client.request(metodo, ruta, content=json.dumps(cuerpo), headers={"content-type": "application/json"})


@pytest.mark.parametrize("via, campo", [
    *(("lote", c) for c in BUENOS), *(("cambio", c) for c in ("descripción", "origen", "ncm")),
    *(("uso", c) for c in BUENOS)])
def test_una_entrada_mala_da_400_o_se_limpia_sin_perder_el_lote(client, via, campo):
    """El NUL se saca, el medio par y lo que no es texto dan 400 sin escribir
    nada, y null es vacío; en todos los campos y vías."""
    url = f"/api/catalog/{VENDOR_ID}/productos"
    cuerpo = {CLAVES[c]: v for c, v in BUENOS.items()}
    fallas = []
    for nombre, volver_malo in MALOS.items():
        cid = _cliente(client)
        owner = _dueno(cid)
        malo = volver_malo(BUENOS[campo])
        if via == "cambio":
            # La fila arranca con otro valor en el campo, para ver si el cambio se aplicó.
            otro = "CN" if campo == "origen" else "73181500"
            client.post(url, json={"vendor_name": VENDOR, "productos": [{**cuerpo, CLAVES[campo]: otro}]})
            antes = _filas(owner)
            clave = _sql("select product_key from vendor_catalog_products where owner_username=:o", o=owner)[0][0]
            r = _mandar(client, "PUT", f"{url}/{clave}",
                        {{"descripción": "descripcion_original"}.get(campo, CLAVES[campo]): malo})
        elif via == "lote":
            item = {k: v for k, v in cuerpo.items() if k != "vendor_name"}
            lote = {"vendor_name": VENDOR, "productos": [{"descripcion": "ARANDELA", "ncm": NCM}, item]}
            (lote if campo == "proveedor" else item)[CLAVES[campo]] = malo
            antes = []
            r = _mandar(client, "POST", url, lote)
        else:
            antes = []
            r = _mandar(client, "POST", "/api/ncm/guardar-uso", {**cuerpo, "client_id": cid, CLAVES[campo]: malo})

        filas = _filas(owner)
        valores = [v for f in filas for v in f]
        lote_entero = via != "lote" or "ARANDELA" in valores
        if nombre == "nulo":
            ok = r.status_code == 200 and lote_entero and BUENOS[campo] in valores \
                and not any("\x00" in str(v) for v in valores)
        elif nombre == "null":
            ok = r.status_code == 200 and lote_entero and not {"None", "False", "[]"} & {v for v in valores if isinstance(v, str)}
        else:
            motivo = "Hay un carácter que no se puede guardar." if nombre == "medio par" \
                else f"{QUE[campo]} tiene que ser texto."
            if via == "lote" and campo != "proveedor":
                motivo = ("Producto 2: " if campo == "descripción" else "Producto 2 («TUERCA»): ") + motivo
            sin_historial = _sql("select count(*) from ncm_historial where owner_username=:o", o=owner) == [(0,)]
            ok = (r.status_code, r.json().get("detail")) == (400, motivo) and filas == antes \
                and (via == "cambio" or sin_historial)
        if not ok:
            fallas.append(f"{nombre}: {r.status_code} {r.text[:100]} filas {filas}")
    assert not fallas, fallas


@pytest.mark.parametrize("via", ["lote", "cambio"])
def test_un_precio_que_no_es_finito_no_rompe_la_lectura_del_catalogo(client, via):
    """La lectura arma JSON estricto: un precio NaN o infinito guardado la rompe."""
    url = f"/api/catalog/{VENDOR_ID}/productos"
    fallas = []
    for valor in ("nan", "inf", "-Infinity", float("inf"), float("nan"), 10 ** 400, "12.5"):
        owner = _dueno(_cliente(client))
        producto = {"descripcion": "TUERCA", "ncm": NCM}
        if via == "lote":
            r = _mandar(client, "POST", url, {"vendor_name": VENDOR, "productos": [{**producto, "valor_unitario": valor}]})
        else:
            client.post(url, json={"vendor_name": VENDOR, "productos": [{**producto, "valor_unitario": 3}]})
            r = _mandar(client, "PUT", f"{url}/tuerca", {"precio_ref": valor})
        lectura = client.get(f"/api/catalog/{VENDOR_ID}")
        precios = [p.get("precio_ref") for p in lectura.json()["productos"].values()] if lectura.status_code == 200 else None
        esperado = [12.5] if valor == "12.5" else [None if via == "lote" else 3]
        if (r.status_code, lectura.status_code, precios) != (200, 200, esperado):
            fallas.append(f"{str(valor)[:20]}: {r.status_code}, lectura {lectura.status_code} {lectura.text[:80]}, {precios}")
    assert not fallas, fallas


def _escribir(consulta, **params):
    from sqlalchemy import text
    from proyecto_maria.database.connection import engine

    async def _run():
        async with engine.begin() as conn:
            await conn.execute(text(consulta), params)
    asyncio.new_event_loop().run_until_complete(_run())


@pytest.mark.parametrize("descripcion", ["螺丝钉", "🔩🔩", "螺丝🔩"])
def test_una_fila_vieja_sin_letras_latinas_queda_una_sola_y_editable(client, descripcion):
    """Una fila de antes guardó la descripción sin letras latinas con la clave
    latina que tenía: después del arranque, guardarla otra vez no la duplica."""
    owner = _dueno(_cliente(client))
    url = f"/api/catalog/{VENDOR_ID}/productos"
    assert client.post(url, json={"vendor_name": VENDOR, "productos": [
        {"descripcion": "VIEJO", "ncm": NCM}]}).status_code == 200
    _escribir("update vendor_catalog_products set descripcion=:d where owner_username=:o", d=descripcion, o=owner)
    with TestClient(main.app):  # el arranque de verdad, con sus migraciones
        pass

    r = client.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": descripcion, "ncm": "73181600"}]})
    assert r.status_code == 200, r.text
    claves = _sql("select product_key from vendor_catalog_products where owner_username=:o", o=owner)
    assert len(claves) == 1, f"«{descripcion}» quedó en {len(claves)} filas: {claves}"
    r = client.put(f"{url}/{claves[0][0]}", json={"origen": "CN"})
    assert r.status_code == 200, r.text
    assert _filas(owner) == [(VENDOR, descripcion, "73181600", "CN")]


def test_una_fila_vieja_que_la_migracion_no_mueve_sigue_editable(client):
    """Si la clave de hoy ya es de otra fila, la vieja queda con la suya y se
    sigue pudiendo cambiar sin tocar la descripción."""
    owner = _dueno(_cliente(client))
    url = f"/api/catalog/{VENDOR_ID}/productos"
    assert client.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": "VIEJO"}]}).status_code == 200
    _escribir("update vendor_catalog_products set descripcion='螺丝钉' where owner_username=:o", o=owner)
    assert client.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": "螺丝钉"}]}).status_code == 200
    with TestClient(main.app):
        pass

    claves = [c for (c,) in _sql("select product_key from vendor_catalog_products where owner_username=:o "
                                 "order by id", o=owner)]
    assert claves[0] == "viejo" and claves[1].startswith("~"), claves
    r = client.put(f"{url}/viejo", json={"origen": "CN"})
    assert r.status_code == 200, f"la fila vieja no se pudo cambiar: {r.status_code} {r.text[:120]}"
    assert [o for (*_, o) in _filas(owner)] == ["CN", None]
