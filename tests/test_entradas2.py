"""Un número, un texto o un parámetro de ruta que llega de afuera no da 500 en
la operación manual, los clientes, guardar al cliente, agrupar y el alta de
estudio.

Lo que sólo rompe en Postgres (NUL, surrogate, entero de más de 32 bits,
32767 parámetros) está en `scripts/testing/entradas2_postgres.py`.
"""
import uuid

import pytest
from sqlalchemy import func, select

from tests.test_entradas1 import _post
from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    _bearer, _consulta, _login, _sin_limites, _tablas, _usuario,
)
from proyecto_maria.database.models import Client, Operation, OperationItem


def _sesion():
    u, _ = _usuario()
    return u, _bearer(_login(u))


def _cliente(sesion, **campos):
    r = _post("/api/clientes", {"nombre": "C", **campos}, sesion)
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _operaciones(u):
    async def _f(s):
        return (await s.execute(select(func.count(Operation.id)).where(Operation.owner_username == u))).scalar()
    return _consulta(_f)


def _items(operation_id):
    async def _f(s):
        return (await s.execute(select(OperationItem).where(OperationItem.operation_id == operation_id))).scalars().all()
    return _consulta(_f)


def _cliente_guardado(cid):
    async def _f(s):
        return (await s.execute(select(Client).where(Client.id == cid))).scalars().first()
    return _consulta(_f)


def _manual(sesion, cid, items):
    cuerpo = '{"client_id": "%s", "items": [%s]}' % (cid, items)
    return _post("/api/operations/manual", cuerpo.encode(), sesion)


NUMEROS_MALOS = {
    "nan": '{"descripcion": "D", "cantidad": NaN, "valor_unitario": 1}',
    "infinito": '{"descripcion": "D", "cantidad": 1e999, "valor_unitario": 1}',
    "menos_infinito": '{"descripcion": "D", "cantidad": 1, "valor_unitario": -Infinity}',
    "texto": '{"descripcion": "D", "cantidad": "abc"}',
    "total_que_desborda": '{"descripcion": "D", "cantidad": 1e200, "valor_unitario": 1e200}',
}


@pytest.mark.parametrize("item", NUMEROS_MALOS.values(), ids=list(NUMEROS_MALOS))
def test_manual_con_numero_no_valido_da_400_y_no_guarda(item):
    u, sesion = _sesion()
    cid = _cliente(sesion)
    r = _manual(sesion, cid, item)
    assert r.status_code == 400, r.text
    assert "número" in r.json()["detail"]
    assert _operaciones(u) == 0


NO_OBJETOS = {
    "cuerpo_lista": b'[{"client_id": "x"}]',
    "item_texto": None,
}


@pytest.mark.parametrize("caso", NO_OBJETOS, ids=list(NO_OBJETOS))
def test_manual_con_algo_que_no_es_objeto_da_400(caso):
    u, sesion = _sesion()
    cid = _cliente(sesion)
    r = _manual(sesion, cid, '"D"') if NO_OBJETOS[caso] is None else _post(
        "/api/operations/manual", NO_OBJETOS[caso], sesion)
    assert r.status_code == 400, r.text
    assert "objeto" in r.json()["detail"]
    assert _operaciones(u) == 0


# campo del ítem enviado → (columna, lo que queda guardado)
GUARDABLES = {
    "nul_en_descripcion": ('{"descripcion": "D\\u0000x", "cantidad": 1}', "descripcion", "D�x"),
    "surrogate_en_pieza": ('{"pieza": "P\\ud800", "descripcion": "D", "cantidad": 1}', "pieza", "P�"),
    "pieza_mas_larga_que_su_columna": ('{"pieza": "%s", "descripcion": "D", "cantidad": 1}' % ("9" * 25),
                                       "pieza", "9" * 20),
    "grupo_id_fuera_de_rango": ('{"descripcion": "D", "cantidad": 1, "grupo_id": 99999999999}', "grupo_id", None),
}


@pytest.mark.parametrize("item,columna,guardado", GUARDABLES.values(), ids=list(GUARDABLES))
def test_manual_guarda_lo_de_afuera_en_la_forma_que_entra_en_su_columna(item, columna, guardado):
    _, sesion = _sesion()
    r = _manual(sesion, _cliente(sesion), item)
    assert r.status_code == 200, r.text
    assert r.json()["items"][0][columna] == guardado
    assert getattr(_items(r.json()["operation_id"])[0], columna) == guardado


@pytest.mark.parametrize("texto", ["x\x00y", "x\ud800y"], ids=["nul", "surrogate"])
@pytest.mark.parametrize("via", ["alta", "edicion"])
def test_texto_del_cliente_que_no_se_puede_guardar_queda_con_reemplazo(via, texto):
    _, sesion = _sesion()
    cuerpo = {"nombre": texto, "notas": texto}
    if via == "alta":
        r = _post("/api/clientes", cuerpo, sesion)
    else:
        r = _post(f"/api/clientes/{_cliente(sesion)}", cuerpo, sesion, metodo="PUT")
    assert r.status_code == 200, r.text
    guardado = _cliente_guardado(r.json()["cliente"]["id"])
    assert (guardado.name, guardado.notes) == ("x�y", "x�y")


def test_editar_cliente_con_el_email_de_otro_da_409_y_no_cambia_nada():
    _, sesion = _sesion()
    _cliente(sesion, email="otro@example.com")
    cid = _cliente(sesion, email="propio@example.com")
    r = _post(f"/api/clientes/{cid}", {"nombre": "Cambiado", "email": "otro@example.com"}, sesion, metodo="PUT")
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "Ya tenés un cliente con el email otro@example.com"
    guardado = _cliente_guardado(cid)
    assert (guardado.name, guardado.email) == ("C", "propio@example.com")


GUARDAR_MALOS = {
    "nan_en_items": b'{"items": [{"descripcion": "D", "cantidad": NaN}]}',
    "nan_en_resumen": b'{"items": [], "resumen": {"valor_total": NaN}}',
    "resumen_items_de_texto": b'{"items": [], "resumen": {"items": "abc"}}',
    "resumen_items_enorme": b'{"items": [], "resumen": {"items": 99999999999}}',
}


@pytest.mark.parametrize("cuerpo", GUARDAR_MALOS.values(), ids=list(GUARDAR_MALOS))
def test_guardar_al_cliente_con_numero_no_valido_da_400_y_no_guarda(cuerpo):
    u, sesion = _sesion()
    r = _post(f"/api/clientes/{_cliente(sesion)}/operaciones", cuerpo, sesion)
    assert r.status_code == 400, r.text
    assert _operaciones(u) == 0


@pytest.mark.parametrize("metodo,ruta", [
    ("GET", "/api/clientes/a%00b"),
    ("POST", "/api/operacion/a%00b/agrupar"),
])
def test_nul_en_la_ruta_da_404_antes_de_llegar_a_la_ruta(metodo, ruta):
    # Sin sesión: si llegara a la ruta, daría 401.
    r = _post(ruta, b"{}", metodo=metodo)
    assert (r.status_code, r.json()) == (404, {"detail": "Not Found"})


def test_agrupar_con_mas_ids_de_los_que_acepta_da_422():
    _, sesion = _sesion()
    r = _post("/api/operacion/no-existe/agrupar", {"item_ids": [str(i) for i in range(10001)]}, sesion)
    assert r.status_code == 422, r.text


def test_alta_de_estudio_pide_la_misma_clave_que_el_registro():
    u = "ent2_" + uuid.uuid4().hex[:10]
    r = _post("/api/organizations/create",
              {"name": "Estudio", "username": u, "password": "abcdefgh", "email": f"{u}@example.com"})
    assert (r.status_code, r.json()["detail"]) == (400, "La contraseña debe incluir al menos un número o símbolo")
