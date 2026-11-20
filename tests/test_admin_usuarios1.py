"""El admin ve cada cuenta con su plan y sus créditos, y mirar no cambia nada.

Las cuentas se siembran con un prefijo propio y se buscan por él: la base de
la suite la comparten todas las pruebas. Cada cuenta lleva secretos con
valores únicos, para buscarlos en el texto entero de la respuesta.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text

from proyecto_maria import main
from proyecto_maria.database.connection import AsyncSessionLocal, engine
from proyecto_maria.database.models import Invitation, Organization, PasswordResetToken, User

RUTA = "/api/admin/usuarios"
PREFIJO = "adus" + uuid.uuid4().hex[:8]
AHORA = datetime.now(timezone.utc).replace(microsecond=0)
EN_10_DIAS = AHORA + timedelta(days=10)
EN_5_DIAS = AHORA + timedelta(days=5)
AYER = AHORA - timedelta(days=1)
RECARGA = AHORA - timedelta(days=3)
ESTUDIO = f"Estudio {PREFIJO}"
ESTUDIO_VENCIDO = f"Estudio vencido {PREFIJO}"

# usuario → (campos de la cuenta, lo que muestra la lista)
CUENTAS = {
    "vigentes": (
        dict(plan="premium", billing_status="active", trial_ends_at=EN_10_DIAS, ops_used_this_period=3,
             extra_ops_remaining=5, extra_ops_expires_at=EN_10_DIAS, last_topup_at=RECARGA),
        dict(plan="premium", cobro="active", cobro_hasta=EN_10_DIAS, operaciones_del_periodo=3,
             creditos_extra=5, creditos_vencen=EN_10_DIAS, ultima_recarga=RECARGA,
             estudio=None, saldo_del_estudio=False, admin=False),
    ),
    "vencidos": (
        dict(plan="premium", billing_status="active", ops_used_this_period=15,
             extra_ops_remaining=7, extra_ops_expires_at=AYER, last_topup_at=RECARGA),
        dict(plan="premium", cobro="active", cobro_hasta=None, operaciones_del_periodo=15,
             creditos_extra=0, creditos_vencen=None, ultima_recarga=RECARGA,
             estudio=None, saldo_del_estudio=False, admin=False),
    ),
    "sin": (
        dict(plan="trial", billing_status="trial", trial_ends_at=EN_5_DIAS, ops_used_this_period=0,
             extra_ops_remaining=0),
        dict(plan="trial", cobro="trial", cobro_hasta=EN_5_DIAS, operaciones_del_periodo=0,
             creditos_extra=0, creditos_vencen=None, ultima_recarga=None,
             estudio=None, saldo_del_estudio=False, admin=False),
    ),
    # Lo suyo no cuenta: gasta lo del estudio.
    "integrante": (
        dict(plan="trial", billing_status="past_due", ops_used_this_period=1,
             extra_ops_remaining=99, extra_ops_expires_at=EN_10_DIAS, last_topup_at=AYER),
        dict(plan="premium", cobro="trial", cobro_hasta=EN_5_DIAS, operaciones_del_periodo=9,
             creditos_extra=4, creditos_vencen=EN_5_DIAS, ultima_recarga=RECARGA,
             estudio=ESTUDIO, saldo_del_estudio=True, admin=False),
    ),
    # Su estudio ya no está: paga ella, como al cobrar.
    "colgada": (
        dict(plan="basico", billing_status="active", ops_used_this_period=4, extra_ops_remaining=2,
             extra_ops_expires_at=EN_10_DIAS),
        dict(plan="basico", cobro="active", cobro_hasta=None, operaciones_del_periodo=4,
             creditos_extra=2, creditos_vencen=EN_10_DIAS, ultima_recarga=None,
             estudio=None, saldo_del_estudio=False, admin=False),
    ),
    # Lo suyo está vigente, lo del estudio vencido: vale lo del estudio.
    "del_vencido": (
        dict(plan="basico", billing_status="active", ops_used_this_period=2,
             extra_ops_remaining=6, extra_ops_expires_at=EN_10_DIAS, last_topup_at=AYER),
        dict(plan="premium", cobro="active", cobro_hasta=None, operaciones_del_periodo=11,
             creditos_extra=0, creditos_vencen=None, ultima_recarga=RECARGA,
             estudio=ESTUDIO_VENCIDO, saldo_del_estudio=True, admin=False),
    ),
    "jefa": (
        dict(plan="premium", billing_status="active", roles=["admin"], ops_used_this_period=2),
        dict(plan="premium", cobro="active", cobro_hasta=None, operaciones_del_periodo=2,
             creditos_extra=0, creditos_vencen=None, ultima_recarga=None,
             estudio=None, saldo_del_estudio=False, admin=True),
    ),
    # Un rol que contiene «admin» no es admin.
    "administrador": (
        dict(plan="premium", billing_status="active", roles=["administrador"]),
        dict(plan="premium", cobro="active", cobro_hasta=None, operaciones_del_periodo=0,
             creditos_extra=0, creditos_vencen=None, ultima_recarga=None,
             estudio=None, saldo_del_estudio=False, admin=False),
    ),
}
# estudio → (nombre, campos, integrante)
ESTUDIOS = {
    "estudio": (ESTUDIO, dict(plan="premium", billing_status="trial", trial_ends_at=EN_5_DIAS,
                              ops_used_this_period=9, extra_ops_remaining=4, extra_ops_expires_at=EN_5_DIAS,
                              last_topup_at=RECARGA), "integrante"),
    "estudio_vencido": (ESTUDIO_VENCIDO, dict(plan="premium", billing_status="active", ops_used_this_period=11,
                                              extra_ops_remaining=8, extra_ops_expires_at=AYER,
                                              last_topup_at=RECARGA), "del_vencido"),
}


def _secretos(de):
    """Valores que no tienen que salir, únicos por cuenta."""
    return dict(payment_customer_id=f"CLIENTEMP-{de}", last_payment_id=f"PAGOMP-{de}",
                mp_preapproval_id=f"PREAPROB-{de}", mp_plan_id=f"PLANMP-{de}",
                payment_method_last4="Q7Z9", payment_method_brand=f"MARCA-{de}")


def _usuario(clave):
    return f"{PREFIJO}_{clave}"


def _todos_los_secretos():
    vistos = []
    for clave in CUENTAS:
        vistos += [f"HASH-{clave}-{PREFIJO}", f"JTI{clave}{PREFIJO}"[:32], f"CANCELA-{clave}-{PREFIJO}",
                   f"RECUPERA-{clave}-{PREFIJO}"]
        vistos += [v for v in _secretos(f"{clave}-{PREFIJO}").values()]
    for clave in ESTUDIOS:
        vistos += [v for v in _secretos(f"{clave}-{PREFIJO}").values()]
    return vistos + [f"INVITA-{PREFIJO}"]


@pytest.fixture(scope="module")
def sembradas():
    ids = {clave: str(uuid.uuid4()) for clave in ESTUDIOS}

    async def _sembrar():
        async with AsyncSessionLocal() as db:
            for clave, (campos, _) in CUENTAS.items():
                db.add(User(username=_usuario(clave), email=f"{_usuario(clave)}@prueba.cdi",
                            password=f"HASH-{clave}-{PREFIJO}", active_jti=f"JTI{clave}{PREFIJO}"[:32],
                            cancelar_sin_confirmar=f"CANCELA-{clave}-{PREFIJO}", is_verified=True,
                            **_secretos(f"{clave}-{PREFIJO}"), **campos))
            await db.flush()
            for clave, (nombre, campos, integrante) in ESTUDIOS.items():
                db.add(Organization(id=ids[clave], name=nombre, owner_username=_usuario(integrante),
                                    **_secretos(f"{clave}-{PREFIJO}"), **campos))
            await db.flush()
            de_quien = {integrante: ids[clave] for clave, (_, _, integrante) in ESTUDIOS.items()}
            for clave, org in (*de_quien.items(), ("colgada", f"borrado-{PREFIJO}")):
                await db.execute(text("UPDATE users SET organization_id = :o WHERE username = :u"),
                                 {"o": org, "u": _usuario(clave)})
            for clave in CUENTAS:
                db.add(PasswordResetToken(user_username=_usuario(clave), token=f"RECUPERA-{clave}-{PREFIJO}",
                                          expires_at=EN_10_DIAS))
            db.add(Invitation(org_id=ids["estudio"], email=f"nueva-{PREFIJO}@prueba.cdi", token=f"INVITA-{PREFIJO}",
                              expires_at=EN_10_DIAS))
            await db.commit()
    asyncio.run(_sembrar())
    # La foto se saca al sembrar: los otros casos también miran, en cualquier orden.
    return _filas()


def _como(usuario):
    if usuario is None:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    else:
        main.app.dependency_overrides[main.get_current_user] = lambda: dict(usuario)


ADMIN = {"username": "admin_adus", "roles": ["admin"], "effective_owner": "admin_adus",
         "plan": "premium", "billing_status": "active"}
COMUN = {"username": "comun_adus", "roles": ["operador"], "effective_owner": "comun_adus",
         "plan": "premium", "billing_status": "active"}


def _pedir(usuario=ADMIN, **params):
    _como(usuario)
    try:
        # Con with: el router de admin se monta al arrancar la app.
        with TestClient(main.app) as client:
            return client.get(RUTA, params={"buscar": PREFIJO, **params})
    finally:
        _como(None)


FECHAS = {"cobro_hasta", "creditos_vencen", "ultima_recarga"}


def _fecha(valor):
    # Sin zona, el navegador la leería como hora local.
    assert valor is None or valor.endswith("+00:00"), valor
    return valor and datetime.fromisoformat(valor)


@pytest.mark.parametrize("quien, codigo", [(None, 401), (COMUN, 403), (ADMIN, 200)],
                         ids=["sin_sesion", "no_admin", "admin"])
def test_quien_pide_la_lista(sembradas, sin_bypass_de_test, quien, codigo):
    r = _pedir(quien)
    assert r.status_code == codigo, r.text[:300]
    if codigo != 200:
        assert PREFIJO not in r.text, r.text[:300]


def test_cada_cuenta_se_ve_con_su_saldo(sembradas):
    r = _pedir()
    assert r.status_code == 200, r.text[:300]
    vistas = {c["usuario"]: c for c in r.json()["usuarios"]}
    for clave, (_, esperado) in CUENTAS.items():
        cuenta = vistas.get(_usuario(clave))
        assert cuenta, f"{clave}: no está en la lista ({sorted(vistas)})"
        assert cuenta["email"] == f"{_usuario(clave)}@prueba.cdi", clave
        visto = {k: _fecha(cuenta[k]) if k in FECHAS else cuenta[k] for k in esperado}
        assert visto == esperado, f"{clave}: {visto}"


PROHIBIDAS = {"password", "active_jti", "token", "payment_customer_id", "last_payment_id",
              "mp_preapproval_id", "mp_plan_id", "payment_method_last4", "payment_method_brand",
              "cancelar_sin_confirmar"}


def _claves(valor):
    if isinstance(valor, dict):
        for k, v in valor.items():
            yield k
            yield from _claves(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from _claves(v)


def test_la_respuesta_no_trae_nada_secreto(sembradas):
    r = _pedir()
    assert r.status_code == 200 and len(r.json()["usuarios"]) == len(CUENTAS), r.text[:300]
    assert not PROHIBIDAS & set(_claves(r.json())), sorted(PROHIBIDAS & set(_claves(r.json())))
    salidos = [s for s in _todos_los_secretos() if s in r.text]
    assert not salidos, salidos


def _filas():
    async def _leer():
        async with AsyncSessionLocal() as db:
            filas = []
            for tabla, columna in (("users", "username"), ("organizations", "name"),
                                   ("password_reset_tokens", "token"), ("invitations", "token")):
                res = await db.execute(text(f"SELECT * FROM {tabla} WHERE {columna} LIKE :p ORDER BY 1"),
                                       {"p": f"%{PREFIJO}%"})
                filas.append([tuple(f) for f in res])
            return filas
    return asyncio.run(_leer())


def test_mirar_no_cambia_la_base(sembradas):
    assert len(sembradas[0]) == len(CUENTAS) and len(sembradas[1]) == len(ESTUDIOS), sembradas
    assert _pedir().status_code == 200
    assert _filas() == sembradas


def test_la_lista_va_por_paginas(sembradas):
    todas = sorted(_usuario(c) for c in CUENTAS)
    vistas = []
    for desde in range(0, len(todas), 2):
        r = _pedir(desde=desde, cuantos=2)
        assert r.status_code == 200 and r.json()["total"] == len(todas), r.text[:300]
        vistas += [c["usuario"] for c in r.json()["usuarios"]]
    assert vistas == todas
    assert _pedir(cuantos=10_000).status_code == 422
    assert _pedir(desde=10**20).status_code == 422


# búsqueda → cuentas que encuentra: sin distinguir mayúsculas; % y _ son letras, no comodines
BUSQUEDAS = {PREFIJO.upper() + "_JEFA": ["jefa"], PREFIJO + "_vi%tes": [], PREFIJO + "_vigente_": [],
             PREFIJO + "_sin@PRUEBA": ["sin"]}


@pytest.fixture
def like_distingue_mayusculas():
    # Como en Postgres: el LIKE de SQLite no distingue mayúsculas y taparía una búsqueda que sí.
    def pragma(valor):
        return lambda conexion, *_: conexion.cursor().execute(f"PRAGMA case_sensitive_like = {valor}")
    prender, apagar = pragma("ON"), pragma("OFF")
    event.listen(engine.sync_engine.pool, "checkout", prender)
    event.listen(engine.sync_engine.pool, "checkin", apagar)
    yield
    event.remove(engine.sync_engine.pool, "checkout", prender)
    event.remove(engine.sync_engine.pool, "checkin", apagar)


def test_la_busqueda_por_usuario_o_email(sembradas, like_distingue_mayusculas):
    for buscar, claves in BUSQUEDAS.items():
        r = _pedir(buscar=buscar)
        assert r.status_code == 200, r.text[:300]
        assert [c["usuario"] for c in r.json()["usuarios"]] == [_usuario(c) for c in claves], buscar
    sin_cuantos = _pedir(buscar="")
    assert sin_cuantos.status_code == 200 and len(sin_cuantos.json()["usuarios"]) <= 50, sin_cuantos.text[:300]
