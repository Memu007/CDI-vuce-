"""GUARDAR-2 (D32 b): la sugerencia no pierde la SIM completa del proveedor.

Desde GUARDAR-1 el historial del cliente guarda el NCM de 8 dígitos
(`84714900`). Si el catálogo del proveedor tiene, para el mismo producto, la
SIM completa que empieza con esos 8 (`84714900100D`), la sugerencia del
cliente usa la del proveedor: antes la pantalla recibía `84714900` y marcaba
incompleto lo que llegaba listo. Vale para `/api/catalog/lookup` (el
autorrelleno de la subida) y `/api/ncm/sugerir`. Contra Postgres:
scripts/testing/guardar2_postgres.py.
"""
import pytest

from tests.test_guardar1 import SIM, _cliente, _guardar, _historial
from tests.test_prelaunch_block2 import _register, _unique, client  # noqa: F401
import proyecto_maria.main as main_mod

PROVEEDOR = "Proveedor de prueba"
DESC = "COMPUTADORA PORTATIL"


@pytest.mark.parametrize("cliente, proveedor, sale", [
    ("84714900", SIM, SIM),
    ("8471.49.00", "8471.49.00.100D", SIM),        # la SIM sale en la forma de siempre
    ("84714900", "8471 49 00 100d", SIM),
    ("84714900", "84714900", "84714900"),          # el proveedor tampoco tiene la SIM
    ("84714900", "84713012100K", "84714900"),      # otra NCM: gana el cliente
    ("84714900", "84714900100", "84714900"),       # sin letra de control no es SIM completa
    ("84714900", None, "84714900"),
    ("8471490010", "84714900100D", "8471490010"),  # el cliente no tiene 8 dígitos
    ("8471X900", "84714900100D", "8471X900"),
])
def test_cual_gana(cliente, proveedor, sale):
    assert main_mod._ncm_del_cliente_o_sim_del_proveedor(cliente, proveedor) == sale


def _con_proveedor(client, ncm_proveedor, desc_proveedor=DESC):
    """Un cliente que recuerda 84714900 y un proveedor con `ncm_proveedor`."""
    cid = _cliente(client)
    assert _guardar(client, cid, [{"pieza": SIM, "ncm": SIM, "descripcion": DESC}]).status_code == 200
    assert _historial(cid) == {DESC: "84714900"}
    r = client.post("/api/catalog/proveedor_de_prueba/productos", json={
        "vendor_name": PROVEEDOR, "productos": [{"descripcion": desc_proveedor, "ncm": ncm_proveedor}]})
    assert r.status_code == 200, r.text
    return cid


def _lookup(client, cid):
    r = client.post("/api/catalog/lookup", json={
        "items": [{"descripcion": DESC}], "vendor_name": PROVEEDOR, "client_id": cid})
    assert r.status_code == 200, r.text
    return r.json()["items"][0]


def _sugerir(client, cid, monkeypatch):
    monkeypatch.setattr(main_mod, "_suggest_ncm_with_gemini", lambda *a, **k: [])
    r = client.post("/api/ncm/sugerir", json={
        "descripcion": DESC, "client_id": cid, "vendor_name": PROVEEDOR})
    assert r.status_code == 200, r.text
    return r.json()["sugerencias"]


def test_el_autorrelleno_trae_la_sim_del_proveedor(client):
    item = _lookup(client, _con_proveedor(client, SIM))
    assert (item["source"], item["ncm"]) == ("cliente", SIM)


def test_la_sugerencia_trae_la_sim_del_proveedor(client, monkeypatch):
    sugerencias = _sugerir(client, _con_proveedor(client, SIM), monkeypatch)
    assert [(s["source"], s["ncm"]) for s in sugerencias][:1] == [("historial", SIM)]


def test_con_otra_ncm_en_el_proveedor_gana_el_cliente(client, monkeypatch):
    cid = _con_proveedor(client, "84713012100K")
    item = _lookup(client, cid)
    assert (item["source"], item["ncm"]) == ("cliente", "84714900")
    ncms = [s["ncm"] for s in _sugerir(client, cid, monkeypatch)]
    assert ncms[:2] == ["84714900", "84713012100K"]


def test_sin_proveedor_queda_el_ncm_del_cliente(client, monkeypatch):
    cid = _con_proveedor(client, SIM)
    r = client.post("/api/catalog/lookup", json={"items": [{"descripcion": DESC}], "client_id": cid})
    assert r.json()["items"][0]["ncm"] == "84714900"
    monkeypatch.setattr(main_mod, "_suggest_ncm_with_gemini", lambda *a, **k: [])
    r = client.post("/api/ncm/sugerir", json={"descripcion": DESC, "client_id": cid})
    assert r.json()["sugerencias"][0]["ncm"] == "84714900"


def test_si_falla_el_catalogo_del_proveedor_queda_la_sugerencia_del_cliente(client, monkeypatch):
    cid = _con_proveedor(client, SIM)
    from proyecto_maria.core import catalog_service as catalog_svc

    async def _falla(*a, **k):
        raise RuntimeError("catálogo caído")

    monkeypatch.setattr(catalog_svc, "match_items", _falla)
    assert [(s["source"], s["ncm"]) for s in _sugerir(client, cid, monkeypatch)] == [("historial", "84714900")]


def test_la_sim_de_otro_producto_parecido_no_gana(client, monkeypatch):
    # El catálogo del proveedor encuentra por parecido otro producto (le falta
    # «INOXIDABLE»): no es el que recuerda el cliente y su SIM no se usa.
    cliente_desc, otro = "TORNILLO ACERO M6 HEXAGONAL INOXIDABLE", "TORNILLO ACERO M6 HEXAGONAL"
    cid = _cliente(client)
    assert _guardar(client, cid, [{"pieza": "73181500900Z", "descripcion": cliente_desc}]).status_code == 200
    client.post("/api/catalog/proveedor_de_prueba/productos", json={
        "vendor_name": PROVEEDOR, "productos": [{"descripcion": otro, "ncm": "73181500900Z"}]})
    r = client.post("/api/catalog/lookup", json={
        "items": [{"descripcion": cliente_desc}], "vendor_name": PROVEEDOR, "client_id": cid})
    assert r.json()["items"][0]["ncm"] == "73181500"
    monkeypatch.setattr(main_mod, "_suggest_ncm_with_gemini", lambda *a, **k: [])
    r = client.post("/api/ncm/sugerir", json={
        "descripcion": cliente_desc, "client_id": cid, "vendor_name": PROVEEDOR})
    assert [s["ncm"] for s in r.json()["sugerencias"]][:1] == ["73181500"]


def test_la_sim_del_proveedor_sale_en_la_forma_de_siempre(client):
    item = _lookup(client, _con_proveedor(client, "8471 49 00 100d"))
    assert item["ncm"] == SIM


# Negativos por dueño: el catálogo del proveedor y el historial del cliente
# son de cada despachante. Lo de otro no se filtra ni cambia la SIM.

def _catalogo_de_otro_usuario(client, ncm=SIM):
    """Registra otro despachante (queda su sesión) con su catálogo del proveedor."""
    _register(client, _unique("g2otro"))
    r = client.post("/api/catalog/proveedor_de_prueba/productos", json={
        "vendor_name": PROVEEDOR, "productos": [{"descripcion": DESC, "ncm": ncm}]})
    assert r.status_code == 200, r.text


def test_el_catalogo_de_otro_usuario_no_cambia_la_sim(client, monkeypatch):
    _catalogo_de_otro_usuario(client)
    cid = _cliente(client)  # otro despachante, sin catálogo propio de ese proveedor
    assert _guardar(client, cid, [{"pieza": SIM, "ncm": SIM, "descripcion": DESC}]).status_code == 200
    item = _lookup(client, cid)
    assert (item["source"], item["ncm"]) == ("cliente", "84714900")
    sugerencias = _sugerir(client, cid, monkeypatch)
    assert [(s["source"], s["ncm"]) for s in sugerencias] == [("historial", "84714900")]


def test_el_historial_de_un_cliente_ajeno_no_se_usa(client, monkeypatch):
    cid = _con_proveedor(client, SIM)  # cliente y catálogo del primer despachante
    _catalogo_de_otro_usuario(client)
    # El segundo pide con el client_id del primero: sólo ve su propio catálogo.
    item = _lookup(client, cid)
    assert (item["source"], item["ncm"]) == ("proveedor", SIM)
    assert "veces_usado" not in item
    sugerencias = _sugerir(client, cid, monkeypatch)
    assert [(s["source"], s["ncm"]) for s in sugerencias] == [("proveedor", SIM)]
    # Sin proveedor no queda nada del primero.
    r = client.post("/api/catalog/lookup", json={"items": [{"descripcion": DESC}], "client_id": cid})
    assert r.status_code == 200, r.text
    assert (r.json()["items"][0]["source"], r.json()["items"][0]["ncm"]) == ("ninguno", None)


def test_el_historial_de_otro_cliente_del_mismo_despachante_no_se_usa(client, monkeypatch):
    """Dos clientes del mismo despachante, con igual nombre y CUIT; sólo uno
    tiene historial. El otro no recibe su sugerencia, ni en el autorrelleno
    ni en /api/ncm/sugerir (agregado de la PM a GUARDAR-2)."""
    cid = _cliente(client)
    ficha = client.get(f"/api/clientes/{cid}").json()
    r = client.post("/api/clientes", json={"nombre": ficha["nombre"], "cuit": ficha["cuit"]})
    assert r.status_code == 200, r.text
    otro = r.json()["cliente"]["id"]
    assert otro != cid
    assert _guardar(client, cid, [{"pieza": SIM, "ncm": SIM, "descripcion": DESC}]).status_code == 200
    assert _historial(cid) == {DESC: "84714900"} and _historial(otro) == {}
    # El primero sí la recibe: el caso distingue.
    r = client.post("/api/catalog/lookup", json={"items": [{"descripcion": DESC}], "client_id": cid})
    assert (r.json()["items"][0]["source"], r.json()["items"][0]["ncm"]) == ("cliente", "84714900")
    r = client.post("/api/catalog/lookup", json={"items": [{"descripcion": DESC}], "client_id": otro})
    assert r.status_code == 200, r.text
    assert (r.json()["items"][0]["source"], r.json()["items"][0]["ncm"]) == ("ninguno", None)
    monkeypatch.setattr(main_mod, "_suggest_ncm_with_gemini", lambda *a, **k: [])
    r = client.post("/api/ncm/sugerir", json={"descripcion": DESC, "client_id": otro})
    assert r.status_code == 200, r.text
    assert r.json()["sugerencias"] == []


def _dos_clientes_iguales(client):
    cid = _cliente(client)
    ficha = client.get(f"/api/clientes/{cid}").json()
    r = client.post("/api/clientes", json={"nombre": ficha["nombre"], "cuit": ficha["cuit"]})
    assert r.status_code == 200, r.text
    return cid, r.json()["cliente"]["id"]


def test_guardar_el_mismo_ncm_en_otro_cliente_le_crea_su_propio_historial(client):
    """Lo que guarda un cliente no actualiza la fila de otro del mismo
    despachante, aunque el NCM y la descripción coincidan (adversario Sonnet
    alto: los filtros por cliente del guardado no tenían prueba)."""
    cid, otro = _dos_clientes_iguales(client)
    assert _guardar(client, cid, [{"pieza": SIM, "ncm": SIM, "descripcion": DESC}]).status_code == 200
    assert _guardar(client, otro, [{"pieza": SIM, "ncm": SIM, "descripcion": DESC}]).status_code == 200
    assert _historial(otro) == {DESC: "84714900"}
    assert _historial(cid) == {DESC: "84714900"}


def test_guardar_otro_ncm_con_la_misma_descripcion_en_otro_cliente_no_pisa_al_primero(client):
    cid, otro = _dos_clientes_iguales(client)
    assert _guardar(client, cid, [{"pieza": SIM, "ncm": SIM, "descripcion": DESC}]).status_code == 200
    assert _guardar(client, otro, [{"pieza": "8471.30.12", "ncm": "8471.30.12", "descripcion": DESC}]).status_code == 200
    assert _historial(otro) == {DESC: "84713012"}
    assert _historial(cid) == {DESC: "84714900"}


def test_guardar_uso_con_un_cliente_no_le_sugiere_a_otro_como_suyo(client, monkeypatch):
    """El historial liviano (load_ncm_historial) es del despachante: después de
    guardar-uso con A, sugerir con B puede traerlo como «historial», pero
    nunca con scope «cliente» (devolución de EXCEL-2b, punto 3)."""
    cid, otro = _dos_clientes_iguales(client)
    desc = f"MONITOR {_unique()}"
    r = client.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": SIM, "client_id": cid})
    assert r.status_code == 200 and r.json().get("success") is not False, r.text
    monkeypatch.setattr(main_mod, "_suggest_ncm_with_gemini", lambda *a, **k: [])

    def sugerir(c):
        r = client.post("/api/ncm/sugerir", json={"descripcion": desc, "client_id": c})
        assert r.status_code == 200, r.text
        return [(s["source"], s.get("scope"), s["ncm"]) for s in r.json()["sugerencias"]]
    # A sí lo recibe como suyo: el caso distingue.
    assert sugerir(cid)[0] == ("historial", "cliente", "84714900")
    assert sugerir(otro) == [("historial", None, SIM)]
