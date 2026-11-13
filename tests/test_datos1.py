"""DATOS-1: `/health` honesto (D2), sin detalles de error al público (D6) y
borrar un cliente con presupuesto compartido (D5, D32 (a)).

El borrado con presupuesto compartido sólo daba 500 en Postgres (la clave
foránea de `public_quotes`); acá, en SQLite, se comprueba qué queda y qué no
después de borrar. El caso en Postgres está en
`scripts/testing/datos1_postgres.py`.
"""
import logging
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Operation, OperationItem, PublicQuote
from proyecto_maria.main import app, get_current_user, get_db
from tests.conftest import cuenta_de_prueba
from tests.test_maria7_rechazos_24_10 import _pedido

# El router de presupuestos se monta en el arranque (lifespan), que el
# TestClient sin `with` no corre: igual que en test_pilar_b_quotes.py.
if not any(getattr(r, "path", "").startswith("/api/quotes") for r in app.routes):
    from proyecto_maria.routers import quote_router
    app.include_router(quote_router.router)

SECRETO ='connection to server at "db.interno" failed: password=secreto-datos1'


@pytest.fixture()
def cliente_http(client):
    """Sin re-lanzar las excepciones del servidor: se mira lo que recibe el
    navegador, como en producción."""
    return TestClient(app, raise_server_exceptions=False)


# --- D2: /health ---------------------------------------------------------

def test_health_con_base_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["database"] == "ok"
    assert cuerpo["status"] == "ok"
    assert "db_error" not in cuerpo


class _BaseCaida:
    async def execute(self, *a, **k):
        raise ConnectionRefusedError(SECRETO)


async def _get_db_caida():
    yield _BaseCaida()


def test_health_sin_base_503_sin_el_texto_del_error(cliente_http, caplog):
    app.dependency_overrides[get_db] = _get_db_caida
    try:
        with caplog.at_level(logging.ERROR):
            r = cliente_http.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 503, r.text
    cuerpo = r.json()
    assert cuerpo["database"] == "error"
    assert cuerpo["status"] != "ok"
    assert "db_error" not in cuerpo
    assert "secreto" not in r.text and "db.interno" not in r.text
    assert SECRETO in caplog.text, "el error de la base tiene que quedar en el log"


# --- D6: los 500 sin dev_detail ------------------------------------------

def _usuario_que_falla(exc):
    def _dep():
        raise exc
    return _dep


def test_http_exception_500_sin_dev_detail(cliente_http, caplog):
    app.dependency_overrides[get_current_user] = _usuario_que_falla(
        HTTPException(status_code=500, detail=SECRETO)
    )
    try:
        with caplog.at_level(logging.ERROR):
            r = cliente_http.get("/api/clientes")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert r.status_code == 500
    cuerpo = r.json()
    assert "dev_detail" not in cuerpo
    assert "secreto" not in r.text and "db.interno" not in r.text
    assert cuerpo["detail"].startswith("No pudimos procesar tu solicitud.")
    assert cuerpo["code"] == "internal_error"
    assert SECRETO in caplog.text


def test_excepcion_no_manejada_sin_dev_detail(cliente_http, caplog):
    app.dependency_overrides[get_current_user] = _usuario_que_falla(
        RuntimeError(SECRETO)
    )
    try:
        with caplog.at_level(logging.ERROR):
            r = cliente_http.get("/api/clientes")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert r.status_code == 500
    cuerpo = r.json()
    assert "dev_detail" not in cuerpo
    assert "secreto" not in r.text and "RuntimeError" not in r.text
    assert cuerpo["detail"].startswith("No pudimos procesar tu solicitud.")
    assert cuerpo["code"] == "internal_error"
    assert SECRETO in caplog.text
    assert "RuntimeError" in caplog.text


def test_4xx_sigue_con_su_detail(cliente_http):
    app.dependency_overrides[get_current_user] = _usuario_que_falla(
        HTTPException(status_code=403, detail="Motivo visible para el usuario")
    )
    try:
        r = cliente_http.get("/api/clientes")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert r.status_code == 403
    assert r.json() == {"detail": "Motivo visible para el usuario"}


def test_4xx_de_la_app_sigue_igual(auth_override, cliente_http):
    r = cliente_http.get("/api/clientes/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.json() == {"detail": "Cliente no encontrado"}


# --- D5: borrar un cliente con presupuesto compartido --------------------

def _como(usuario):
    app.dependency_overrides[get_current_user] = lambda: usuario


def _cliente_con_presupuesto(c, creados):
    """Crea un cliente con una operación compartida; devuelve (cliente, op, token).
    Lo anota en `creados` para que la prueba lo retire al terminar."""
    cid = _cliente(c, creados)
    r = _guardar(c, cid)
    assert r.status_code == 200, r.text
    op = r.json()["operation_id"]
    return cid, op, _compartir(c, op)


async def _presupuestos_de(op_id):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(PublicQuote).where(PublicQuote.operation_id == op_id))
        return len(res.scalars().all())


async def _items_de(op_id):
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(OperationItem).where(OperationItem.operation_id == op_id))
        return len(res.scalars().all())


def _usuario_nuevo(base, prefijo):
    u = dict(base)
    u["username"] = u["effective_owner"] = f"{prefijo}_{uuid.uuid4().hex[:8]}"
    return u


# Cada prueba usa dueños propios y no `test_user`: el cupo de operaciones de
# `test_user` lo comparte toda la suite (el plan corta en 15) y gastarlo acá
# hace fallar con 402 a pruebas de otros archivos.
@pytest.fixture()
def dueno(auth_override):
    u = _usuario_nuevo(auth_override, "d1")
    with cuenta_de_prueba(u["username"]):
        yield u


@pytest.fixture()
def otro_usuario(auth_override):
    u = _usuario_nuevo(auth_override, "otro")
    with cuenta_de_prueba(u["username"]):
        yield u


@pytest.fixture()
def creados(cliente_http):
    """Clientes que creó la prueba; al terminar los borra su dueño, y sus
    operaciones quedan sin cliente."""
    lista = []
    yield lista
    app.dependency_overrides.pop(get_db, None)
    for usuario, cid in lista:
        _como(usuario)
        cliente_http.delete(f"/api/clientes/{cid}")


async def test_borrar_cliente_borra_sus_presupuestos_y_no_los_ajenos(
    dueno, otro_usuario, cliente_http, creados
):
    c = cliente_http
    _como(otro_usuario)
    _, op_ajena, token_ajeno = _cliente_con_presupuesto(c, creados)
    _como(dueno)
    cid, op, token = _cliente_con_presupuesto(c, creados)
    _, op_otro_cliente, token_otro_cliente = _cliente_con_presupuesto(c, creados)
    r = _guardar(c, cid)
    assert r.status_code == 200, r.text
    op2 = r.json()["operation_id"]
    borradas = {1: (op, token), 2: (op2, _compartir(c, op2))}
    quedan = {"otro cliente": (op_otro_cliente, token_otro_cliente),
              "otro dueño": (op_ajena, token_ajeno)}
    for o, t in [*borradas.values(), *quedan.values()]:
        assert c.get(f"/api/quotes/public/{t}").status_code == 200
        assert await _items_de(o) > 0

    r = c.delete(f"/api/clientes/{cid}")
    assert r.status_code == 200, r.text

    assert c.get(f"/api/clientes/{cid}").status_code == 404
    for n, (o, t) in borradas.items():
        assert c.get(f"/api/quotes/public/{t}").status_code == 404, f"presupuesto de la operación {n}"
        assert await _presupuestos_de(o) == 0, f"presupuesto de la operación {n}"
        assert await _items_de(o) == 0, f"ítems de la operación {n}"
    for quien, (o, t) in quedan.items():
        assert c.get(f"/api/quotes/public/{t}").status_code == 200, quien
        assert await _items_de(o) > 0, quien


def test_otro_dueno_no_borra_el_cliente_ni_su_presupuesto(
    dueno, otro_usuario, cliente_http, creados
):
    c = cliente_http
    _como(dueno)
    cid, _, token = _cliente_con_presupuesto(c, creados)
    _como(otro_usuario)
    r = c.delete(f"/api/clientes/{cid}")
    assert r.status_code == 404
    _como(dueno)
    assert c.get(f"/api/clientes/{cid}").status_code == 200
    assert c.get(f"/api/quotes/public/{token}").status_code == 200


async def test_si_falla_a_mitad_no_se_borra_nada(dueno, cliente_http, creados):
    """El cliente se borra último: si eso falla, el presupuesto (que ya se
    borró en la misma transacción) tiene que volver."""
    c = cliente_http
    _como(dueno)
    cid, op, token = _cliente_con_presupuesto(c, creados)

    async def _get_db_que_falla_al_final():
        async with AsyncSessionLocal() as s:
            async def _falla(_obj):
                raise RuntimeError("falla simulada al borrar el cliente")
            s.delete = _falla
            yield s

    app.dependency_overrides[get_db] = _get_db_que_falla_al_final
    try:
        r = c.delete(f"/api/clientes/{cid}")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 500
    assert c.get(f"/api/clientes/{cid}").status_code == 200
    assert c.get(f"/api/quotes/public/{token}").status_code == 200
    assert await _presupuestos_de(op) == 1


# --- D141 (a): pasar una operación a otro cliente -------------------------

ITEM = {"pieza": "8471.30.12", "descripcion": "TABLETA SINTETICA", "origen": "CHN",
        "cantidad": 1, "valor_unitario": 50, "peso_unitario": 0.5}


def _cliente(c, creados):
    r = c.post("/api/clientes", json={"nombre": f"PC1_{uuid.uuid4().hex[:8]}"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    creados.append((app.dependency_overrides[get_current_user](), cid))
    return cid


def _guardar(c, cid, opid=None, item=ITEM):
    """Sin `opid` crea una operación nueva; con él, guarda esa en el cliente."""
    cuerpo = {"items": [item]}
    if opid:
        cuerpo["operacion_id"] = opid
    return c.post(f"/api/clientes/{cid}/operaciones", json=cuerpo)


def _compartir(c, op):
    r = c.post("/api/quotes/share", json={"operation_id": op})
    assert r.status_code == 200, r.text
    return r.json()["token"]


async def _cliente_de(op_id):
    async with AsyncSessionLocal() as s:
        return (await s.get(Operation, op_id)).client_id


async def _operacion_sin_cliente(dueno, archivo):
    async with AsyncSessionLocal() as s:
        op = Operation(owner_username=dueno["username"], generated_file=archivo)
        s.add(op)
        await s.commit()
        return op.id


async def test_pasar_la_operacion_a_otro_cliente_borra_su_presupuesto(
    dueno, otro_usuario, cliente_http, creados
):
    """El link compartido es el presupuesto armado para un cliente: pasada a
    otro, la operación deja de mostrarse ahí. Quedarse en el mismo cliente, recibir
    uno por primera vez o fallar a mitad no lo borra."""
    c = cliente_http
    _como(dueno)
    a, b = _cliente(c, creados), _cliente(c, creados)
    op = _guardar(c, a).json()["operation_id"]
    tokens = [_compartir(c, op), _compartir(c, op)]
    otro_op = _guardar(c, a).json()["operation_id"]
    otro_token = _compartir(c, otro_op)
    op_suelta = await _operacion_sin_cliente(dueno, f"MARIA_{uuid.uuid4().hex}.TXT")
    token_suelto = _compartir(c, op_suelta)

    # (cliente, operación, ítem, código, link que tiene que seguir andando)
    pasos = [
        (a, op, ITEM, 200, True),
        (b, op, {**ITEM, "valor_unitario": "NaN"}, 400, True),
        (a, op_suelta, ITEM, 200, True),
        (b, op, ITEM, 200, False),
    ]
    for cid, opid, item, codigo, sigue in pasos:
        r = _guardar(c, cid, opid, item)
        assert r.status_code == codigo, (cid == b, opid == op, r.text)
        assert r.status_code != 200 or r.json()["operation_id"] == opid, "la misma operación"
        esperado = 200 if sigue else 404
        for token in tokens:
            assert c.get(f"/api/quotes/public/{token}").status_code == esperado, (cid == b, codigo)
    assert c.get(f"/api/quotes/public/{otro_token}").status_code == 200, "otra operación del mismo cliente"
    assert await _presupuestos_de(op) == 0
    assert await _cliente_de(op) == b
    assert c.get(f"/api/quotes/public/{token_suelto}").status_code == 200, "sin cliente antes"
    assert await _cliente_de(op_suelta) == a

    # Una operación ajena no se encuentra: el otro dueño crea la suya.
    _como(otro_usuario)
    r = _guardar(c, _cliente(c, creados), otro_op)
    assert r.status_code == 200, r.text
    assert r.json()["operation_id"] != otro_op
    _como(dueno)
    assert c.get(f"/api/quotes/public/{otro_token}").status_code == 200, "otro dueño"
    assert await _cliente_de(otro_op) == a


async def test_borrar_el_cliente_anterior_no_deja_el_link_de_la_operacion_pasada(
    dueno, cliente_http, creados
):
    """Un MARIA generado y guardado en A, pasado a B, ya no es de A: borrar A no
    lo toca y su link no vuelve."""
    c = cliente_http
    _como(dueno)
    a, b = _cliente(c, creados), _cliente(c, creados)
    r = c.post("/generate_maria", json=_pedido())
    assert r.status_code == 200, r.text
    op = r.json()["operacion_id"]
    assert await _cliente_de(op) is None
    assert _guardar(c, a, op).json()["operation_id"] == op
    token = _compartir(c, op)
    assert _guardar(c, b, op).status_code == 200
    assert c.delete(f"/api/clientes/{a}").status_code == 200
    assert c.get(f"/api/quotes/public/{token}").status_code == 404
    assert await _presupuestos_de(op) == 0
    assert await _cliente_de(op) == b
