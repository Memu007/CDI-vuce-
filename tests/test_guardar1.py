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
    NCM_HISTORIAL_MAX, lookup_client_memory, ncm_para_historial,
)

SIM = "84714900100D"


@pytest.mark.parametrize("entra, sale", [
    (SIM, "84714900"),
    ("8471.49.00.100D", "84714900"),
    ("8471.49.00", "8471.49.00"),
    ("84714900", "84714900"),
    ("  84714900  ", "84714900"),
    ("ABCDEFGHIJKLMN", None),
    ("", None),
    (None, None),
])
def test_la_forma_del_ncm_que_guarda_el_historial(entra, sale):
    assert ncm_para_historial(entra) == sale
    assert sale is None or len(sale) <= NCM_HISTORIAL_MAX


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
    assert _historial(cid) == {"COMPUTADORA PORTATIL": "84714900", "TABLETA": "8471.30.12"}


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
    """El historial no puede tirar abajo el guardado: una fila que la base
    rechaza al guardar (acá, sin cliente) no se lleva la operación."""
    import proyecto_maria.services.client_memory as memoria
    from proyecto_maria.database.models import ClientProductHistory

    async def _fila_que_la_base_rechaza(db, **kwargs):
        db.add(ClientProductHistory(owner_username=kwargs["owner_username"], client_id=None,
                                    ncm="1", descripcion="x"))

    monkeypatch.setattr(memoria, "upsert_client_product_history", _fila_que_la_base_rechaza)
    cid = _cliente(client)
    r = _guardar(client, cid, [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL", "valor_unitario": 10}])
    assert r.status_code == 200, r.text
    op = r.json()["operation_id"]
    assert [p for (p,) in _sql("select pieza from operation_items where operation_id=:o", o=op)] == [SIM]
    assert _historial(cid) == {}


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
    r = client.put(f"/api/clientes/{cid}/catalogo/productos/{pid}", json={"ncm": "NO-ES-UN-NCM-VALIDO"})
    assert r.status_code == 400, r.text
    assert _historial(cid) == {"TABLETA": "84714900"}
