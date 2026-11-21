"""Créditos que carga un admin: la regla de acreditar y el registro de cada carga."""

import asyncio
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from proyecto_maria.database.connection import AsyncSessionLocal, engine
from proyecto_maria.database.models import CreditoAdmin, Organization, User
from proyecto_maria.services import billing_service

AHORA = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)
ANTES = AHORA - timedelta(days=3)


def _cuenta(extra, vence):
    return SimpleNamespace(extra_ops_remaining=extra, extra_ops_expires_at=vence, last_topup_at=ANTES)


class _Reloj(datetime):
    @classmethod
    def now(cls, tz=None):
        return AHORA


# (extra, vencimiento, n, entra, vigentes_antes, extra después)
_CARGAS = [
    (0, None, 10, True, 0, 10),
    (None, None, 1, True, 0, 1),
    (90, AHORA + timedelta(days=5), 10, True, 90, 100),
    (91, AHORA + timedelta(days=5), 10, False, 91, 91),
    (5, AHORA - timedelta(seconds=1), 10, True, 0, 10),
    (95, AHORA - timedelta(days=1), 100, True, 0, 100),
    (0, None, 101, False, 0, 0),
]


@pytest.mark.parametrize("extra,vence,n,entra,antes,despues", _CARGAS)
def test_acreditar_extra(monkeypatch, extra, vence, n, entra, antes, despues):
    monkeypatch.setattr(billing_service, "datetime", _Reloj)
    cuenta = _cuenta(extra, vence)
    assert billing_service.acreditar_extra(cuenta, n, AHORA) == (entra, antes)
    assert (cuenta.extra_ops_remaining or 0) == despues
    if entra:
        assert cuenta.extra_ops_expires_at == AHORA + timedelta(days=30)
        assert cuenta.last_topup_at == AHORA
    else:
        assert cuenta.last_topup_at == ANTES


def test_recarga_entra_sin_n_sigue_siendo_una_recarga():
    assert billing_service.recarga_entra(_cuenta(100 - billing_service.TOPUP_OPS, None)) == (
        True, 100 - billing_service.TOPUP_OPS)
    assert billing_service.recarga_entra(_cuenta(101 - billing_service.TOPUP_OPS, None))[0] is False


async def _registrar(**fila):
    async with AsyncSessionLocal() as db:
        db.add(CreditoAdmin(**fila))
        await db.commit()


async def _filas(pedido):
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(CreditoAdmin).where(CreditoAdmin.pedido == pedido))).scalars().all()


async def _borrar(pedido):
    async with AsyncSessionLocal() as db:
        for fila in (await db.execute(select(CreditoAdmin).where(CreditoAdmin.pedido == pedido))).scalars():
            await db.delete(fila)
        await db.commit()


def test_el_pedido_se_registra_una_sola_vez():
    pedido = str(uuid.uuid4())
    fila = dict(pedido=pedido, admin="adm", cuenta="org:1", usuario="u", cantidad=10, vigentes_antes=0)
    try:
        asyncio.run(_registrar(**fila))
        with pytest.raises(IntegrityError):
            asyncio.run(_registrar(**{**fila, "cuenta": "otra", "cantidad": 5}))
        [guardada] = asyncio.run(_filas(pedido))
        assert (guardada.cuenta, guardada.cantidad, guardada.admin) == ("org:1", 10, "adm")
        assert guardada.cargado_en is not None
    finally:
        asyncio.run(_borrar(pedido))


def test_la_tabla_no_tiene_claves_foraneas():
    async def mirar():
        async with engine.connect() as conn:
            return await conn.run_sync(lambda c: inspect(c).get_foreign_keys("creditos_admin"))
    assert asyncio.run(mirar()) == []


# --- La ruta: POST /api/admin/usuarios/{usuario}/creditos ---

RUTA = "/api/admin/usuarios/{}/creditos"
ADMIN = {"username": "admin_adcr", "roles": ["admin"], "effective_owner": "admin_adcr",
         "plan": "premium", "billing_status": "active"}
COMUN = {"username": "comun_adcr", "roles": ["operador"], "effective_owner": "comun_adcr",
         "plan": "premium", "billing_status": "active"}
PROPIOS = 7


def _cuerpo(cantidad, pedido=None, **extra):
    return {"cantidad": cantidad, "pedido": pedido or str(uuid.uuid4()), **extra}


@contextmanager
def _cliente(usuario=ADMIN):
    from proyecto_maria import main
    if usuario is not None:
        main.app.dependency_overrides[main.get_current_user] = lambda: dict(usuario)
    try:
        with TestClient(main.app) as client:  # con with: el router de admin se monta al arrancar
            yield client
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)


@pytest.fixture
def sembrar():
    """Da una función que crea una cuenta (sola o de un estudio) con su saldo; borra todo al final."""
    creadas = []

    def _nueva(extra=0, vence=None, estudio=False):
        nombre = f"adcr{uuid.uuid4().hex[:10]}"
        saldo = dict(extra_ops_remaining=extra, extra_ops_expires_at=vence, last_topup_at=ANTES)
        org = str(uuid.uuid4()) if estudio else None
        creadas.append((nombre, org))

        async def _run():
            async with AsyncSessionLocal() as db:
                propios = dict(extra_ops_remaining=PROPIOS, extra_ops_expires_at=None) if estudio else saldo
                db.add(User(username=nombre, email=f"{nombre}@prueba.cdi", password="x", is_verified=True,
                            plan="premium", billing_status="active", **propios))
                await db.flush()
                if estudio:
                    db.add(Organization(id=org, name=f"Estudio {nombre}", owner_username=nombre,
                                        plan="premium", billing_status="active", **saldo))
                    await db.flush()
                    await db.execute(text("UPDATE users SET organization_id = :o WHERE username = :u"),
                                     {"o": org, "u": nombre})
                await db.commit()
        asyncio.run(_run())
        return nombre

    yield _nueva

    async def _limpiar():
        async with AsyncSessionLocal() as db:
            for nombre, org in creadas:
                await db.execute(text("DELETE FROM creditos_admin WHERE usuario = :u"), {"u": nombre})
                await db.execute(text("UPDATE users SET organization_id = NULL WHERE username = :u"), {"u": nombre})
                if org:
                    await db.execute(text("DELETE FROM organizations WHERE id = :o"), {"o": org})
                await db.execute(text("DELETE FROM users WHERE username = :u"), {"u": nombre})
            await db.commit()
    asyncio.run(_limpiar())


async def _saldo_de(nombre):
    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(User).where(User.username == nombre))).scalars().one()
        org = u.organization_id and await db.get(Organization, u.organization_id)
        foto = lambda c: (c.extra_ops_remaining, c.extra_ops_expires_at and billing_service.como_utc(
            c.extra_ops_expires_at), c.last_topup_at and billing_service.como_utc(c.last_topup_at))
        return foto(u), org and foto(org)


def _registros(nombre):
    async def _run():
        async with AsyncSessionLocal() as db:
            return (await db.execute(select(CreditoAdmin).where(CreditoAdmin.usuario == nombre))).scalars().all()
    return asyncio.run(_run())


def _cerca(valor, esperado):
    assert abs(datetime.fromisoformat(valor) - esperado) < timedelta(minutes=2), (valor, esperado)


AHORA_REAL = lambda: datetime.now(timezone.utc)  # noqa: E731
# (nombre, extra, vence en días (None: sin fecha), estudio, cantidad, vigentes antes, extra después)
_RUTA_CARGAS = [
    ("solo", 0, None, False, 10, 0, 10),
    ("estudio", 0, None, True, 10, 0, 10),
    ("vencidos", 5, -1, False, 10, 0, 10),
    ("llena_el_tope", 90, 5, False, 10, 90, 100),
    ("vencidos_y_cien", 95, -1, True, 100, 0, 100),
]


@pytest.mark.parametrize("extra,vence,estudio,n,antes,despues", [c[1:] for c in _RUTA_CARGAS],
                         ids=[c[0] for c in _RUTA_CARGAS])
def test_carga(sembrar, extra, vence, estudio, n, antes, despues):
    nombre = sembrar(extra, vence is not None and AHORA_REAL() + timedelta(days=vence) or None, estudio)
    cuerpo = _cuerpo(n, admin="otro")
    with _cliente() as c:
        r = c.post(RUTA.format(nombre), json=cuerpo)
        assert r.status_code == 200, r.text
        dato = r.json()
        assert (dato["usuario"], dato["creditos_extra"], dato["ya_aplicado"]) == (nombre, despues, False)
        assert (dato["saldo_del_estudio"], dato["estudio"] is not None) == (estudio, estudio)
        _cerca(dato["creditos_vencen"], AHORA_REAL() + timedelta(days=30))
        _cerca(dato["ultima_recarga"], AHORA_REAL())
        assert dato["carga"] == {"pedido": cuerpo["pedido"], "cantidad": n, "vigentes_antes": antes,
                                 "admin": ADMIN["username"]}
        propio, del_estudio = asyncio.run(_saldo_de(nombre))
        if estudio:
            assert propio[0] == PROPIOS and propio[1] is None and del_estudio[0] == despues
        [fila] = _registros(nombre)
        cuenta = f"org:{_org_de(nombre)}" if estudio else nombre
        assert (fila.admin, fila.cuenta, fila.usuario, fila.cantidad, fila.vigentes_antes) == (
            ADMIN["username"], cuenta, nombre, n, antes)

        otra = c.post(RUTA.format(nombre), json=cuerpo)
    assert otra.status_code == 200, otra.text
    assert otra.json()["ya_aplicado"] is True
    assert otra.json()["creditos_extra"] == despues
    assert asyncio.run(_saldo_de(nombre)) == (propio, del_estudio)
    assert len(_registros(nombre)) == 1


def _org_de(nombre):
    async def _run():
        async with AsyncSessionLocal() as db:
            return (await db.execute(select(User.organization_id).where(User.username == nombre))).scalar_one()
    return asyncio.run(_run())


@pytest.mark.parametrize("extra,n", [(91, 10), (1, 100), (120, 1)])
def test_no_entra(sembrar, extra, n):
    nombre = sembrar(extra, AHORA_REAL() + timedelta(days=5))
    antes = asyncio.run(_saldo_de(nombre))
    with _cliente() as c:
        r = c.post(RUTA.format(nombre), json=_cuerpo(n))
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == (f"Ya tiene {extra} operaciones extra y el tope es 100: "
                                  f"entran como mucho {max(0, 100 - extra)}.")
    assert asyncio.run(_saldo_de(nombre)) == antes
    assert _registros(nombre) == []


@pytest.mark.parametrize("cambio", ["cantidad", "usuario"])
def test_otra_carga_con_el_mismo_pedido(sembrar, cambio):
    nombre, otro = sembrar(), sembrar()
    cuerpo = _cuerpo(10)
    with _cliente() as c:
        assert c.post(RUTA.format(nombre), json=cuerpo).status_code == 200
        antes = asyncio.run(_saldo_de(nombre)), asyncio.run(_saldo_de(otro))
        destino, segundo = (nombre, {**cuerpo, "cantidad": 5}) if cambio == "cantidad" else (otro, cuerpo)
        r = c.post(RUTA.format(destino), json=segundo)
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "ese pedido ya se usó para otra carga"
    assert (asyncio.run(_saldo_de(nombre)), asyncio.run(_saldo_de(otro))) == antes
    assert len(_registros(nombre)) == 1 and _registros(otro) == []


_UUID = "0b5f2a4e-3c1d-4e8f-9a7b-6c5d4e3f2a1b"
_INVALIDOS = [
    {"cantidad": 0, "pedido": _UUID}, {"cantidad": -1, "pedido": _UUID}, {"cantidad": 101, "pedido": _UUID},
    {"cantidad": 1.5, "pedido": _UUID}, {"cantidad": "10", "pedido": _UUID}, {"cantidad": True, "pedido": _UUID},
    {"pedido": _UUID}, {"cantidad": 10, "pedido": "no-es-un-uuid"}, {"cantidad": 10, "pedido": _UUID + "0"},
    {"cantidad": 10, "pedido": _UUID.upper()}, {"cantidad": 10},
]


@pytest.mark.parametrize("cuerpo", _INVALIDOS)
def test_cuerpo_invalido(sembrar, cuerpo):
    nombre = sembrar()
    antes = asyncio.run(_saldo_de(nombre))
    with _cliente() as c:
        r = c.post(RUTA.format(nombre), json=cuerpo)
    assert r.status_code == 422, r.text
    assert asyncio.run(_saldo_de(nombre)) == antes and _registros(nombre) == []


def test_usuario_inexistente():
    with _cliente() as c:
        r = c.post(RUTA.format(f"adcr_nadie_{uuid.uuid4().hex[:6]}"), json=_cuerpo(10))
    assert r.status_code == 404, r.text


@pytest.mark.parametrize("quien,codigo", [(None, 401), (COMUN, 403)], ids=["sin_sesion", "no_admin"])
def test_quien_carga(sembrar, sin_bypass_de_test, quien, codigo):
    nombre = sembrar()
    antes = asyncio.run(_saldo_de(nombre))
    with _cliente(quien) as c:
        r = c.post(RUTA.format(nombre), json=_cuerpo(10))
    assert r.status_code == codigo, r.text
    assert asyncio.run(_saldo_de(nombre)) == antes and _registros(nombre) == []


def test_sin_csrf(sembrar, monkeypatch):
    """Con sesión de cookie, la carga sin el token CSRF no entra."""
    from proyecto_maria import main
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    nombre, admin = sembrar(), f"adcr{uuid.uuid4().hex[:10]}"
    with TestClient(main.app) as c:
        assert c.post("/auth/register", json={"username": admin, "password": "Clave-Segura-123",
                                              "email": f"{admin}@prueba.cdi", "name": admin}).status_code in (200, 201)
        try:
            _fijar_roles(admin, ["admin"])
            assert c.post("/auth/login", json={"username": admin, "password": "Clave-Segura-123"}).status_code == 200
            sin = c.post(RUTA.format(nombre), json=_cuerpo(10))
            assert sin.status_code == 403, sin.text
            assert _registros(nombre) == []
            con = c.post(RUTA.format(nombre), json=_cuerpo(10), headers={"x-csrf-token": c.cookies.get("csrf_token")})
            assert con.status_code == 200, con.text
            assert _registros(nombre)[0].admin == admin
        finally:
            _borrar_usuario(admin)


def _fijar_roles(nombre, roles):
    async def _run():
        async with AsyncSessionLocal() as db:
            u = (await db.execute(select(User).where(User.username == nombre))).scalars().one()
            u.roles = roles
            await db.commit()
    asyncio.run(_run())


def _borrar_usuario(nombre):
    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(text("DELETE FROM users WHERE username = :u"), {"u": nombre})
            await db.commit()
    asyncio.run(_run())
