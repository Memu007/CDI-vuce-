"""GUARDAR-1: guardar una operación con la posición SIM completa no da 500.

En producción (Postgres) `client_product_history.ncm` es String(10) y la SIM
completa (`84714900100D`) no entra: el error saltaba en el commit de
`save_client_operation` y no se guardaba nada. SQLite no controla el largo,
así que acá se prueba la forma que se guarda y que el historial no tira abajo
el guardado; contra Postgres lo prueba scripts/testing/guardar1_postgres.py.
"""
import asyncio

import pytest

from tests.test_prelaunch_block2 import _register, _unique, client  # noqa: F401
from proyecto_maria.database.connection import get_async_session
from proyecto_maria.services.client_memory import (
    lookup_client_memory, ncm_para_historial,
)

SIM = "84714900100D"


@pytest.mark.parametrize("entra, sale", [
    (SIM, "84714900"),
    ("8471.49.00.100D", "84714900"),
    ("8471.49.00", "84714900"),
    ("84714900", "84714900"),
    ("  84714900  ", "84714900"),
    ("ABCDEFGHIJKLMN", None),
    ("", None),
    (None, None),
])
def test_la_forma_del_ncm_que_guarda_el_historial(entra, sale):
    assert ncm_para_historial(entra) == sale
    assert sale is None or len(sale) == 8


def _sql(consulta, **params):
    from sqlalchemy import text

    async def _run():
        async for db in get_async_session():
            return (await db.execute(text(consulta), params)).fetchall()
    return asyncio.new_event_loop().run_until_complete(_run())


def _cliente(client) -> str:
    usuario = _unique("g1")
    _register(client, usuario)
    r = client.post("/api/clientes", json={"nombre": f"Cliente {usuario}", "cuit": "30999999995"})
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _guardar(client, cid, items):
    return client.post(f"/api/clientes/{cid}/operaciones", json={"items": items})


def _historial(cid) -> dict:
    return dict(_sql("select descripcion, ncm from client_product_history where client_id=:c", c=cid))


def test_guardar_con_la_sim_completa_deja_el_ncm_en_el_historial(client):
    cid = _cliente(client)
    r = _guardar(client, cid, [
        {"pieza": SIM, "ncm": SIM, "descripcion": "COMPUTADORA PORTATIL", "cantidad": 1, "valor_unitario": 10},
        {"pieza": "8471.30.12", "ncm": "8471.30.12", "descripcion": "TABLETA", "cantidad": 1, "valor_unitario": 5},
    ])
    assert r.status_code == 200, r.text
    piezas = sorted(p for (p,) in _sql("select pieza from operation_items where operation_id=:o",
                                       o=r.json()["operation_id"]))
    assert piezas == ["8471.30.12", SIM]
    assert _historial(cid) == {"COMPUTADORA PORTATIL": "84714900", "TABLETA": "84713012"}


def test_la_sugerencia_del_cliente_devuelve_el_ncm_de_la_sim(client):
    cid = _cliente(client)
    usuario = _sql("select owner_username from clients where id=:c", c=cid)[0][0]
    assert _guardar(client, cid, [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}]).status_code == 200

    async def _buscar():
        async for db in get_async_session():
            return await lookup_client_memory(db, usuario, cid, "computadora portatil")
    encontrado = asyncio.new_event_loop().run_until_complete(_buscar())
    assert encontrado and encontrado["ncm"] == "84714900", encontrado


def test_si_el_historial_falla_la_operacion_igual_se_guarda(client, monkeypatch):
    """El historial no puede tirar abajo el guardado: si falla hasta su
    commit (acá, una fila sin cliente que se cuela fuera del savepoint), la
    operación ya quedó guardada y contada."""
    import proyecto_maria.main as main_mod
    from proyecto_maria.database.models import ClientProductHistory

    async def _fila_que_la_base_rechaza(db, upsert, **kwargs):
        db.add(ClientProductHistory(owner_username=kwargs["owner_username"], client_id=None,
                                    ncm="1", descripcion="x"))
        return True

    monkeypatch.setattr(main_mod, "_historial_de_un_producto", _fila_que_la_base_rechaza)
    cid = _cliente(client)
    usuario = _sql("select owner_username from clients where id=:c", c=cid)[0][0]
    antes = _sql("select coalesce(ops_used_this_period, 0) from users where username=:u", u=usuario)[0][0]
    r = _guardar(client, cid, [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL", "valor_unitario": 10}])
    assert r.status_code == 200 and r.json()["historial_guardado"] is False, r.text
    op = r.json()["operation_id"]
    assert [p for (p,) in _sql("select pieza from operation_items where operation_id=:o", o=op)] == [SIM]
    assert _historial(cid) == {}
    # y la operación cuenta para el plan aunque el commit del historial falle
    assert _sql("select ops_used_this_period from users where username=:u", u=usuario)[0][0] == antes + 1


def test_la_operacion_cuenta_para_el_plan_aunque_falle_el_historial(client, monkeypatch):
    import proyecto_maria.services.client_memory as memoria

    async def _falla(db, **kwargs):
        raise RuntimeError("simulado")

    monkeypatch.setattr(memoria, "upsert_client_product_history", _falla)
    cid = _cliente(client)
    usuario = _sql("select owner_username from clients where id=:c", c=cid)[0][0]
    antes = _sql("select coalesce(ops_used_this_period, 0) from users where username=:u", u=usuario)[0][0]
    assert _guardar(client, cid, [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}]).status_code == 200
    assert _sql("select ops_used_this_period from users where username=:u", u=usuario)[0][0] == antes + 1


def test_aprender_un_producto_con_la_sim_completa(client):
    cid = _cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn",
                    json={"items": [{"ncm": SIM, "descripcion": "COMPUTADORA PORTATIL"}]})
    assert r.status_code == 200 and r.json()["aprendidos"] == 1, r.text
    assert _historial(cid) == {"COMPUTADORA PORTATIL": "84714900"}


def test_editar_un_producto_con_la_sim_completa_no_deja_un_codigo_cortado(client):
    """Antes se cortaba a 10 caracteres: `8471490010`, un código que no existe."""
    cid = _cliente(client)
    client.post(f"/api/clientes/{cid}/catalogo/productos/learn",
                json={"items": [{"ncm": "84713012", "descripcion": "TABLETA"}]})
    (pid,) = [i for (i,) in _sql("select id from client_product_history where client_id=:c", c=cid)]
    r = client.put(f"/api/clientes/{cid}/catalogo/productos/{pid}", json={"ncm": SIM})
    assert r.status_code == 200, r.text
    assert _historial(cid) == {"TABLETA": "84714900"}
    for malo in ("NO-ES-UN-NCM-VALIDO", "ABC", None, 0, ""):
        r = client.put(f"/api/clientes/{cid}/catalogo/productos/{pid}", json={"ncm": malo})
        assert r.status_code == 400, (malo, r.text)
    assert _historial(cid) == {"TABLETA": "84714900"}


def test_aprender_no_cuenta_lo_que_no_guardo(client):
    cid = _cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn",
                    json={"items": [{"ncm": "SIN-CLASIFICAR", "descripcion": "ALGO"},
                                    {"ncm": SIM, "descripcion": "COMPUTADORA PORTATIL"}]})
    assert r.status_code == 200 and r.json()["aprendidos"] == 1, r.text
    assert _historial(cid) == {"COMPUTADORA PORTATIL": "84714900"}


def test_si_falla_el_contador_del_plan_no_queda_una_operacion_gratis(client, monkeypatch):
    """La operación y el contador del plan van en el mismo commit: si el
    contador falla, la operación no queda guardada con un 500 en pantalla
    (el reintento la duplicaba sin contarla)."""
    from proyecto_maria.services import billing_service

    def _falla(entidad):
        raise RuntimeError("simulado")

    cid = _cliente(client)
    monkeypatch.setattr(billing_service, "record_operation_created", _falla)
    r = _guardar(client, cid, [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}])
    assert r.status_code == 500
    assert _sql("select count(*) from operations where client_id=:c", c=cid)[0][0] == 0


def test_la_respuesta_dice_si_el_historial_no_se_guardo(client, monkeypatch):
    import proyecto_maria.services.client_memory as memoria
    cid = _cliente(client)
    r = _guardar(client, cid, [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}])
    assert r.json().get("historial_guardado") is True, r.json()

    async def _falla(db, **kwargs):
        raise RuntimeError("simulado")
    monkeypatch.setattr(memoria, "upsert_client_product_history", _falla)
    r = _guardar(client, cid, [{"pieza": SIM, "descripcion": "OTRA COSA"}])
    assert r.status_code == 200 and r.json().get("historial_guardado") is False, r.json()


def test_datos_largos_de_la_operacion_no_impiden_guardarla(client):
    """Mismo defecto en otras columnas de largo fijo del mismo guardado
    (Postgres): moneda String(3), origen String(50), fecha de inicio de
    actividades del cliente String(10); y el carácter NUL, que Postgres no
    acepta en un texto. Desde CLIENTE-1c (D15 b) la fecha con hora no se
    copia a la ficha: queda vacía y la operación se guarda igual."""
    cid = _cliente(client)
    r = client.post(f"/api/clientes/{cid}/operaciones", json={
        "currency": "DOLARES", "source": "x" * 80,
        "comprador_fecha_inic_activ": "2020-01-15T00:00:00",
        "items": [{"pieza": SIM, "descripcion": "COMPU\x00TADORA", "origen": "CHN", "grupo_id": "g1"}]})
    assert r.status_code == 200, r.text
    op = r.json()["operation_id"]
    assert _sql("select currency, length(source) from operations where id=:o", o=op) == [("DOL", 50)]
    assert _sql("select descripcion from operation_items where operation_id=:o", o=op) == [("COMPUTADORA",)]
    assert _sql("select fecha_inic_activ from clients where id=:c", c=cid) == [("",)]


def _con_un_producto_que_la_base_rechaza(monkeypatch):
    """El producto «MALO» deja una fila que la base rechaza al escribirla; los
    demás pasan por el historial de verdad."""
    import proyecto_maria.services.client_memory as memoria
    from proyecto_maria.database.models import ClientProductHistory
    real = memoria.upsert_client_product_history

    async def _upsert(db, *args, **kwargs):
        if kwargs.get("descripcion") == "MALO":
            db.add(ClientProductHistory(owner_username=kwargs["owner_username"], client_id=None,
                                        ncm="1", descripcion="x"))
            return None
        return await real(db, *args, **kwargs)
    monkeypatch.setattr(memoria, "upsert_client_product_history", _upsert)


def test_un_producto_malo_no_se_lleva_el_historial_de_los_demas(client, monkeypatch):
    _con_un_producto_que_la_base_rechaza(monkeypatch)
    cid = _cliente(client)
    r = _guardar(client, cid, [{"pieza": "84713012", "descripcion": "TABLETA"},
                               {"pieza": "84714900", "descripcion": "MALO"},
                               {"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}])
    assert r.status_code == 200 and r.json()["historial_guardado"] is False, r.text
    assert _historial(cid) == {"TABLETA": "84713012", "COMPUTADORA PORTATIL": "84714900"}


def test_aprender_con_un_producto_malo_guarda_los_demas(client, monkeypatch):
    _con_un_producto_que_la_base_rechaza(monkeypatch)
    cid = _cliente(client)
    r = client.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "84714900", "descripcion": "MALO"}, {"ncm": SIM, "descripcion": "COMPUTADORA PORTATIL"}]})
    assert r.status_code == 200 and r.json()["aprendidos"] == 1, r.text
    assert _historial(cid) == {"COMPUTADORA PORTATIL": "84714900"}


def test_un_grupo_fuera_de_rango_y_el_nul_en_otros_textos_no_impiden_guardar(client):
    """Postgres: Integer de 32 bits y ningún texto con NUL."""
    cid = _cliente(client)
    r = client.post(f"/api/clientes/{cid}/operaciones", json={
        "comprador_domicilio": "CALLE\x00 1",
        "items": [{"pieza": "8471\x004900", "descripcion": "TABLETA", "origen": "C\x00HN",
                   "unidad": "u\x00", "grupo_id": 2 ** 31}]})
    assert r.status_code == 200, r.text
    op = r.json()["operation_id"]
    assert _sql("select pieza, origen, unidad, grupo_id from operation_items where operation_id=:o", o=op) \
        == [("84714900", "CHN", "u", None)]
    assert _sql("select address from clients where id=:c", c=cid) == [("CALLE 1",)]
