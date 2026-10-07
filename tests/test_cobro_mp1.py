"""COBRO-MP-1: el aviso de pago de Mercado Pago se aplica una sola vez.

Pasos 1 y 3 del plan (PARA-PM.md):
1. Cada pago se aplica una vez: alternar dos pagos viejos reales (el ataque
   de D8, por el aviso IPN sin firma) no renueva ni suma recargas.
3. Un pago de plan extiende el período desde su fin, si la cuenta sigue
   activa, en vez de fijar 30 días desde hoy.

Mercado Pago simulado: ni el SDK real ni internet.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401

PAGOS: dict = {}


class _Pagos:
    def get(self, pid):
        return {"status": 200, "response": PAGOS[str(pid)]}


class _SDK:
    def __init__(self, token):
        pass

    def payment(self):
        return _Pagos()


@pytest.fixture(autouse=True)
def _mp(monkeypatch):
    import proyecto_maria.main as main_mod
    monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", "secreto-de-prueba")
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
    monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setattr(main_mod.mercadopago, "SDK", _SDK)
    PAGOS.clear()


def _pago(pid: str, referencia: str, monto: float = 45000.0) -> str:
    PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": referencia,
                  "transaction_amount": monto, "currency_id": "ARS", "payer": {"id": "payer-1"}}
    return pid


def _aviso_ipn(client, pid: str):
    """El aviso IPN, sin firma: cualquiera lo puede mandar sin sesión."""
    client.cookies.clear()
    return client.post(f"/api/payments/webhook?topic=payment&id={pid}")


def _fin(usuario: dict) -> datetime:
    fin = usuario["trial_ends_at"]
    if isinstance(fin, str):
        fin = datetime.fromisoformat(fin)
    return fin if fin.tzinfo else fin.replace(tzinfo=timezone.utc)


def test_alternar_dos_pagos_viejos_no_renueva(client):
    """El ataque de D8: con dos pagos reales ya aplicados, alternarlos dejaba
    la cuenta vencida otra vez activa 30 días y con el contador en 0."""
    usuario = _unique("mp1_alt")
    _register(client, usuario)
    a = _pago(f"pa-{usuario}", f"{usuario}:premium")
    b = _pago(f"pb-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, a).status_code == 200
    assert _aviso_ipn(client, b).status_code == 200

    vencida = datetime.now(timezone.utc) - timedelta(days=40)
    _set_user(usuario, billing_status="past_due", trial_ends_at=vencida, ops_used_this_period=999)
    for pid in (a, b, a, b):
        r = _aviso_ipn(client, pid)
        assert r.status_code == 200, r.text[:300]
    despues = _get_user(usuario)
    assert despues["billing_status"] == "past_due", despues
    assert despues["ops_used_this_period"] == 999, despues


def test_una_recarga_reenviada_no_suma_operaciones(client):
    usuario = _unique("mp1_rec")
    _register(client, usuario)
    t = _pago(f"pt-{usuario}", f"{usuario}:topup", monto=10000.0)
    u = _pago(f"pu-{usuario}", f"{usuario}:premium")
    for pid in (t, u):
        assert _aviso_ipn(client, pid).status_code == 200
    extra = _get_user(usuario)["extra_ops_remaining"]
    for pid in (t, u, t):
        assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["extra_ops_remaining"] == extra


def test_el_pago_aplicado_queda_registrado(client):
    from proyecto_maria.database.models import PagoMercadoPagoAplicado  # noqa: F401
    from tests.test_prelaunch_block2 import asyncio
    from proyecto_maria.database.connection import AsyncSessionLocal
    from sqlalchemy.future import select

    usuario = _unique("mp1_reg")
    _register(client, usuario)
    pid = _pago(f"pr-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200

    async def _leer():
        async with AsyncSessionLocal() as db:
            fila = (await db.execute(select(PagoMercadoPagoAplicado).where(
                PagoMercadoPagoAplicado.payment_id == pid))).scalar_one()
            return fila.cuenta, fila.tipo, float(fila.monto), fila.moneda
    assert asyncio.new_event_loop().run_until_complete(_leer()) == (usuario, "premium", 45000.0, "ARS")


def test_pagar_con_la_cuenta_activa_extiende_desde_el_fin(client):
    """Pagar antes de que venza no pierde los días que quedaban."""
    usuario = _unique("mp1_ext")
    _register(client, usuario)
    fin_actual = datetime.now(timezone.utc) + timedelta(days=20)
    _set_user(usuario, billing_status="active", plan="premium", trial_ends_at=fin_actual)
    pid = _pago(f"pe-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    nuevo = _fin(_get_user(usuario))
    assert abs((nuevo - (fin_actual + timedelta(days=30))).total_seconds()) < 120, nuevo


def test_pagar_con_la_cuenta_vencida_cuenta_desde_hoy(client):
    usuario = _unique("mp1_ven")
    _register(client, usuario)
    _set_user(usuario, billing_status="past_due", trial_ends_at=datetime.now(timezone.utc) - timedelta(days=10))
    pid = _pago(f"pv-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    despues = _get_user(usuario)
    assert despues["billing_status"] == "active"
    falta = _fin(despues) - datetime.now(timezone.utc)
    assert timedelta(days=29) < falta <= timedelta(days=30), falta


def _org(usuario: str, **campos) -> str:
    """Una organización del usuario, escrita directo en la base."""
    import asyncio
    import uuid
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import Organization
    org_id = str(uuid.uuid4())

    async def _crear():
        async for db in get_async_session():
            db.add(Organization(id=org_id, name=f"Estudio {usuario}", owner_username=usuario, **campos))
            await db.commit()
            return
    asyncio.new_event_loop().run_until_complete(_crear())
    return org_id


def _leer_org(org_id: str, **cambios) -> dict:
    import asyncio
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import Organization
    leido = {}

    async def _run():
        async for db in get_async_session():
            org = await db.get(Organization, org_id)
            for k, v in cambios.items():
                setattr(org, k, v)
            await db.commit()
            leido.update(billing_status=org.billing_status, trial_ends_at=org.trial_ends_at,
                         ops_used_this_period=org.ops_used_this_period,
                         extra_ops_remaining=org.extra_ops_remaining)
            return
    asyncio.new_event_loop().run_until_complete(_run())
    return leido


def test_organizacion_alternar_dos_pagos_viejos_no_renueva(client):
    usuario = _unique("mp1_org")
    _register(client, usuario)
    org_id = _org(usuario)
    a = _pago(f"poa-{usuario}", f"org:{org_id}:premium")
    b = _pago(f"pob-{usuario}", f"org:{org_id}:premium")
    t = _pago(f"pot-{usuario}", f"org:{org_id}:topup", monto=10000.0)
    for pid in (a, b, t):
        assert _aviso_ipn(client, pid).status_code == 200
    vencida = datetime.now(timezone.utc) - timedelta(days=40)
    extra = _leer_org(org_id, billing_status="past_due", trial_ends_at=vencida,
                      ops_used_this_period=999)["extra_ops_remaining"]
    for pid in (a, b, t, a, b, t):
        assert _aviso_ipn(client, pid).status_code == 200
    despues = _leer_org(org_id)
    assert despues["billing_status"] == "past_due", despues
    assert despues["ops_used_this_period"] == 999, despues
    assert despues["extra_ops_remaining"] == extra, despues


def test_organizacion_pagar_activa_extiende_desde_el_fin(client):
    usuario = _unique("mp1_orge")
    _register(client, usuario)
    fin_actual = datetime.now(timezone.utc) + timedelta(days=20)
    org_id = _org(usuario, billing_status="active", plan="premium", trial_ends_at=fin_actual)
    pid = _pago(f"poe-{usuario}", f"org:{org_id}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    nuevo = _fin(_leer_org(org_id))
    assert abs((nuevo - (fin_actual + timedelta(days=30))).total_seconds()) < 120, nuevo


# ── Paso 2: el monto se controla (D29 b) ─────────────────────────────

class _Suscripciones:
    def get(self, pid):
        if pid not in SUSCRIPCIONES:
            return {"status": 500, "response": {"message": "simulado: Mercado Pago no contesta"}}
        return {"status": 200, "response": SUSCRIPCIONES[pid]}


SUSCRIPCIONES: dict = {}
_SDK.preapproval = lambda self: _Suscripciones()


@pytest.fixture(autouse=True)
def _sin_suscripciones():
    SUSCRIPCIONES.clear()


def _leer_pago(pid: str):
    import asyncio
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import PagoMercadoPagoAplicado
    leido = {}

    async def _run():
        async for db in get_async_session():
            fila = await db.get(PagoMercadoPagoAplicado, pid)
            if fila is not None:
                leido.update(estado=fila.estado, motivo=fila.motivo,
                             monto_esperado=fila.monto_esperado, cuenta=fila.cuenta)
            return
    asyncio.new_event_loop().run_until_complete(_run())
    return leido


def _vencida(usuario: str):
    _set_user(usuario, billing_status="past_due",
              trial_ends_at=datetime.now(timezone.utc) - timedelta(days=3))


def test_un_plan_pagado_de_menos_no_se_aplica_y_queda_rechazado(client):
    usuario = _unique("mp2_menos")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pm-{usuario}", f"{usuario}:premium", monto=30000.0)
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200, r.text
    assert "rechazado" in r.json().get("skipped", ""), r.json()
    assert _get_user(usuario)["billing_status"] == "past_due"
    fila = _leer_pago(pid)
    assert fila["estado"] == "rechazado" and fila["monto_esperado"] == 45000.0, fila
    assert "30000" in fila["motivo"] and "45000" in fila["motivo"], fila
    # reenviarlo no lo vuelve a evaluar ni lo aplica
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"


def test_un_plan_en_otra_moneda_no_se_aplica(client):
    usuario = _unique("mp2_usd")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pu-{usuario}", f"{usuario}:premium", monto=45000.0)
    PAGOS[pid]["currency_id"] = "USD"
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_una_recarga_pagada_de_menos_no_suma(client):
    usuario = _unique("mp2_rec")
    _register(client, usuario)
    antes = _get_user(usuario)["extra_ops_remaining"] or 0
    pid = _pago(f"pr-{usuario}", f"{usuario}:topup", monto=5000.0)
    assert _aviso_ipn(client, pid).status_code == 200
    assert (_get_user(usuario)["extra_ops_remaining"] or 0) == antes
    assert _leer_pago(pid)["estado"] == "rechazado"


@pytest.mark.parametrize("monto, aplica", [(45000.0, True), (44999.0, False)])
def test_un_link_viejo_sin_precio_se_compara_con_el_precio_de_hoy(client, monto, aplica):
    """D29, condición 1: los links armados antes de este cambio no traen el
    precio; se usa el de hoy."""
    usuario = _unique("mp2_viejo")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pv-{usuario}", f"{usuario}:premium", monto=monto)
    assert "metadata" not in PAGOS[pid]
    assert _aviso_ipn(client, pid).status_code == 200
    assert (_get_user(usuario)["billing_status"] == "active") is aplica


def test_un_link_con_el_precio_de_cuando_se_armo_se_respeta(client):
    """D29 (b): si el precio subió después de armar el link, el pago vale."""
    usuario = _unique("mp2_link")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pl-{usuario}", f"{usuario}:premium", monto=40000.0)
    PAGOS[pid]["metadata"] = {"precio_esperado": 40000.0}
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"
    assert _leer_pago(pid)["estado"] == "aplicado"


def test_el_link_de_pago_guarda_el_precio(monkeypatch):
    from proyecto_maria.services import billing_service

    armados = []

    class _Pref:
        def create(self, datos):
            armados.append(datos)
            return {"status": 201, "response": {"id": "pref-1", "init_point": "x"}}

    class _SDKPref:
        def preference(self):
            return _Pref()

    monkeypatch.setattr(billing_service, "_get_sdk", lambda: _SDKPref())
    monkeypatch.setattr(billing_service, "_preapproval_plan_id", lambda plan: None)

    class _U:
        username, email = "ana", "ana@example.com"

    billing_service.create_checkout(_U(), "premium")
    billing_service.create_topup_checkout(_U())
    assert armados[0]["metadata"]["precio_esperado"] == billing_service.PLANS["premium"]["price"]
    assert armados[1]["metadata"]["precio_esperado"] == billing_service.TOPUP_PRICE_ARS


def _pago_de_suscripcion(usuario: str, monto: float, ref_suscripcion=None, pre="pre-1"):
    pid = _pago(f"ps-{usuario}-{monto}", f"{usuario}:premium", monto=monto)
    PAGOS[pid]["metadata"] = {"preapproval_id": f"{pre}-{usuario}"}
    SUSCRIPCIONES[f"{pre}-{usuario}"] = {
        "id": f"{pre}-{usuario}", "status": "authorized",
        "external_reference": ref_suscripcion or f"{usuario}:premium",
        "auto_recurring": {"transaction_amount": 30000.0, "currency_id": "ARS"},
    }
    return pid


def test_una_suscripcion_se_compara_con_su_monto_en_mercado_pago(client):
    """D29, condición 2: en la suscripción el precio está en el panel de
    Mercado Pago, no en PLANS; un panel más barato no rechaza el cobro."""
    usuario = _unique("mp2_sus")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 30000.0)
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"
    assert _leer_pago(pid)["monto_esperado"] == 30000.0


def test_una_suscripcion_pagada_de_menos_no_se_aplica(client):
    usuario = _unique("mp2_susm")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 20000.0)
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_la_suscripcion_de_otra_cuenta_no_vale(client):
    usuario = _unique("mp2_suso")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 30000.0, ref_suscripcion="otro_usuario:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_si_no_se_puede_leer_la_suscripcion_mercado_pago_reintenta(client):
    """Un error pasajero no deja el pago rechazado para siempre."""
    usuario = _unique("mp2_susf")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 30000.0)
    SUSCRIPCIONES.clear()
    assert _aviso_ipn(client, pid).status_code == 503
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"


def test_emi_ve_los_pagos_rechazados_y_un_usuario_comun_no(client, monkeypatch):
    """D29, condición 3: un pago rechazado es un cliente que pagó y no
    recibió nada; el admin lo ve en el panel."""
    usuario = _unique("mp2_ve")
    _register(client, usuario)
    pid = _pago(f"pa-{usuario}", f"{usuario}:premium", monto=100.0)
    assert _aviso_ipn(client, pid).status_code == 200

    admin = _unique("mp2_admin")
    monkeypatch.setenv("ADMIN_USERNAMES", admin)
    _register(client, admin)
    r = client.get("/api/dev/pagos-mp-rechazados")
    assert r.status_code == 200, r.text
    fila = next(p for p in r.json()["pagos"] if p["payment_id"] == pid)
    assert fila["cuenta"] == usuario and fila["monto"] == 100.0 and fila["monto_esperado"] == 45000.0
    assert fila["motivo"]

    client.cookies.clear()
    _register(client, _unique("mp2_comun"))
    assert client.get("/api/dev/pagos-mp-rechazados").status_code == 403


def test_el_panel_muestra_los_pagos_rechazados():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "proyecto_maria/templates/dev_dashboard.html").read_text()
    assert "/api/dev/pagos-mp-rechazados" in html
    assert "Pagos de Mercado Pago no aplicados" in html


# ── D31: no se aplica dos veces aunque lleguen a la vez ──────────────

def test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez(client, monkeypatch):
    """Los dos avisos pasan el «¿ya está?» antes de que alguno guarde: lo que
    frena el segundo es la clave primaria de mp_pagos_aplicados al guardar."""
    import asyncio
    import httpx
    import proyecto_maria.main as main_mod

    usuario = _unique("mp1_doble")
    _register(client, usuario)
    pid = _pago(f"pd-{usuario}", f"{usuario}:topup", monto=10000.0)
    antes = _get_user(usuario)["extra_ops_remaining"] or 0

    original = main_mod._registrar_pago_mp
    pasaron = []

    async def _los_dos_pasan_antes_de_guardar(*args, **kwargs):
        estado = await original(*args, **kwargs)
        pasaron.append(estado)
        for _ in range(500):
            if len(pasaron) >= 2:
                break
            await asyncio.sleep(0.01)
        return estado

    monkeypatch.setattr(main_mod, "_registrar_pago_mp", _los_dos_pasan_antes_de_guardar)

    async def _dos_a_la_vez():
        transporte = httpx.ASGITransport(app=main_mod.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test") as c:
            url = f"/api/payments/webhook?topic=payment&id={pid}"
            return await asyncio.gather(c.post(url), c.post(url))

    respuestas = asyncio.new_event_loop().run_until_complete(_dos_a_la_vez())
    assert pasaron == ["aplicado", "aplicado"], pasaron  # los dos pasaron el «¿ya está?»
    assert [r.status_code for r in respuestas] == [200, 200], [r.text[:200] for r in respuestas]
    salteados = [r.json().get("skipped") for r in respuestas]
    assert salteados.count("payment_id ya procesado") == 1 and salteados.count(None) == 1, salteados
    assert (_get_user(usuario)["extra_ops_remaining"] or 0) == antes + 10
    assert _leer_pago(pid)["estado"] == "aplicado"
