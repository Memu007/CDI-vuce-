"""COBRO-MP-1: el aviso de pago de Mercado Pago se aplica una sola vez.

Pasos 1 y 3 del plan (PARA-PM.md):
1. Cada pago se aplica una vez: alternar dos pagos viejos reales (el ataque
   de D8, por el aviso IPN sin firma) no renueva ni suma recargas.
3. Un pago de plan extiende el período desde su fin, si la cuenta sigue
   activa, en vez de fijar 30 días desde hoy.

Mercado Pago simulado: ni el SDK real ni internet.
"""
from datetime import datetime, timedelta, timezone

import pytest

from tests.mp_firma import aviso_firmado
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
                  "transaction_amount": monto, "currency_id": "ARS", "payer": {"id": "payer-1"},
                  "date_approved": datetime.now(timezone.utc).isoformat()}
    return pid


def _aviso_pago(client, pid: str):
    """El aviso de pago firmado, sin sesión, como lo manda Mercado Pago."""
    client.cookies.clear()
    return client.post("/api/payments/webhook", **aviso_firmado("payment", pid, "secreto-de-prueba"))


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
    assert _aviso_pago(client, a).status_code == 200
    assert _aviso_pago(client, b).status_code == 200

    vencida = datetime.now(timezone.utc) - timedelta(days=40)
    _set_user(usuario, billing_status="past_due", trial_ends_at=vencida, ops_used_this_period=999)
    for pid in (a, b, a, b):
        r = _aviso_pago(client, pid)
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
        assert _aviso_pago(client, pid).status_code == 200
    extra = _get_user(usuario)["extra_ops_remaining"]
    for pid in (t, u, t):
        assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["extra_ops_remaining"] == extra


def test_el_pago_aplicado_queda_registrado(client):
    from proyecto_maria.database.models import PagoMercadoPagoAplicado  # noqa: F401
    from tests.test_prelaunch_block2 import asyncio
    from proyecto_maria.database.connection import AsyncSessionLocal
    from sqlalchemy.future import select

    usuario = _unique("mp1_reg")
    _register(client, usuario)
    pid = _pago(f"pr-{usuario}", f"{usuario}:premium")
    assert _aviso_pago(client, pid).status_code == 200

    async def _leer():
        async with AsyncSessionLocal() as db:
            fila = (await db.execute(select(PagoMercadoPagoAplicado).where(
                PagoMercadoPagoAplicado.payment_id == pid))).scalar_one()
            return fila.cuenta, fila.tipo, float(fila.monto), fila.moneda
    assert asyncio.run(_leer()) == (usuario, "premium", 45000.0, "ARS")


def test_pagar_con_la_cuenta_activa_extiende_desde_el_fin(client):
    """Pagar antes de que venza no pierde los días que quedaban."""
    usuario = _unique("mp1_ext")
    _register(client, usuario)
    fin_actual = datetime.now(timezone.utc) + timedelta(days=20)
    _set_user(usuario, billing_status="active", plan="premium", trial_ends_at=fin_actual)
    pid = _pago(f"pe-{usuario}", f"{usuario}:premium")
    assert _aviso_pago(client, pid).status_code == 200
    nuevo = _fin(_get_user(usuario))
    assert abs((nuevo - (fin_actual + timedelta(days=30))).total_seconds()) < 120, nuevo


def test_pagar_con_la_cuenta_vencida_cuenta_desde_hoy(client):
    usuario = _unique("mp1_ven")
    _register(client, usuario)
    _set_user(usuario, billing_status="past_due", trial_ends_at=datetime.now(timezone.utc) - timedelta(days=10))
    pid = _pago(f"pv-{usuario}", f"{usuario}:premium")
    assert _aviso_pago(client, pid).status_code == 200
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
    asyncio.run(_crear())
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
    asyncio.run(_run())
    return leido


def test_organizacion_alternar_dos_pagos_viejos_no_renueva(client):
    usuario = _unique("mp1_org")
    _register(client, usuario)
    org_id = _org(usuario)
    a = _pago(f"poa-{usuario}", f"org:{org_id}:premium")
    b = _pago(f"pob-{usuario}", f"org:{org_id}:premium")
    t = _pago(f"pot-{usuario}", f"org:{org_id}:topup", monto=10000.0)
    for pid in (a, b, t):
        assert _aviso_pago(client, pid).status_code == 200
    vencida = datetime.now(timezone.utc) - timedelta(days=40)
    extra = _leer_org(org_id, billing_status="past_due", trial_ends_at=vencida,
                      ops_used_this_period=999)["extra_ops_remaining"]
    for pid in (a, b, t, a, b, t):
        assert _aviso_pago(client, pid).status_code == 200
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
    assert _aviso_pago(client, pid).status_code == 200
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
    asyncio.run(_run())
    return leido


def _vencida(usuario: str):
    _set_user(usuario, billing_status="past_due",
              trial_ends_at=datetime.now(timezone.utc) - timedelta(days=3))


def test_un_plan_pagado_de_menos_no_se_aplica_y_queda_rechazado(client):
    usuario = _unique("mp2_menos")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pm-{usuario}", f"{usuario}:premium", monto=30000.0)
    r = _aviso_pago(client, pid)
    assert r.status_code == 200, r.text
    assert "rechazado" in r.json().get("skipped", ""), r.json()
    assert _get_user(usuario)["billing_status"] == "past_due"
    fila = _leer_pago(pid)
    assert fila["estado"] == "rechazado" and fila["monto_esperado"] == 45000.0, fila
    assert "30000" in fila["motivo"] and "45000" in fila["motivo"], fila
    # reenviarlo no lo vuelve a evaluar ni lo aplica
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"


def test_un_plan_en_otra_moneda_no_se_aplica(client):
    usuario = _unique("mp2_usd")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pu-{usuario}", f"{usuario}:premium", monto=45000.0)
    PAGOS[pid]["currency_id"] = "USD"
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_una_recarga_pagada_de_menos_no_suma(client):
    usuario = _unique("mp2_rec")
    _register(client, usuario)
    antes = _get_user(usuario)["extra_ops_remaining"] or 0
    pid = _pago(f"pr-{usuario}", f"{usuario}:topup", monto=5000.0)
    assert _aviso_pago(client, pid).status_code == 200
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
    assert _aviso_pago(client, pid).status_code == 200
    assert (_get_user(usuario)["billing_status"] == "active") is aplica


def test_un_link_con_el_precio_de_cuando_se_armo_se_respeta(client):
    """D29 (b): si el precio subió después de armar el link, el pago vale."""
    usuario = _unique("mp2_link")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pl-{usuario}", f"{usuario}:premium", monto=40000.0)
    PAGOS[pid]["metadata"] = {"precio_esperado": 40000.0}
    assert _aviso_pago(client, pid).status_code == 200
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
    # Sin punto: un id de pago de Mercado Pago no lo lleva.
    pid = _pago(f"ps-{usuario}-{int(monto)}", f"{usuario}:premium", monto=monto)
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
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"
    assert _leer_pago(pid)["monto_esperado"] == 30000.0


def test_una_suscripcion_pagada_de_menos_no_se_aplica(client):
    usuario = _unique("mp2_susm")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 20000.0)
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_la_suscripcion_de_otra_cuenta_no_vale(client):
    usuario = _unique("mp2_suso")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 30000.0, ref_suscripcion="otro_usuario:premium")
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_si_no_se_puede_leer_la_suscripcion_mercado_pago_reintenta(client):
    """Un error pasajero no deja el pago rechazado para siempre."""
    usuario = _unique("mp2_susf")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 30000.0)
    SUSCRIPCIONES.clear()
    assert _aviso_pago(client, pid).status_code == 503
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"


def test_emi_ve_los_pagos_rechazados_y_un_usuario_comun_no(client):
    """D29, condición 3: un pago rechazado es un cliente que pagó y no
    recibió nada; el admin lo ve en el panel."""
    usuario = _unique("mp2_ve")
    _register(client, usuario)
    pid = _pago(f"pa-{usuario}", f"{usuario}:premium", monto=100.0)
    assert _aviso_pago(client, pid).status_code == 200

    admin = _unique("mp2_admin")
    _register(client, admin)
    _set_user(admin, roles=["admin"])
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
            aviso = aviso_firmado("payment", pid, "secreto-de-prueba")
            url = "/api/payments/webhook"
            return await asyncio.gather(c.post(url, **aviso), c.post(url, **aviso))

    respuestas = asyncio.run(_dos_a_la_vez())
    assert pasaron == ["aplicado", "aplicado"], pasaron  # los dos pasaron el «¿ya está?»
    assert [r.status_code for r in respuestas] == [200, 200], [r.text[:200] for r in respuestas]
    salteados = [r.json().get("skipped") for r in respuestas]
    assert salteados.count("payment_id ya procesado") == 1 and salteados.count(None) == 1, salteados
    assert (_get_user(usuario)["extra_ops_remaining"] or 0) == antes + 10
    assert _leer_pago(pid)["estado"] == "aplicado"


# ── Paso 4: renovaciones de la suscripción (D30 a) ───────────────────
# El cobro autorizado (/authorized_payments/{id}) tiene la forma de la
# documentación pública de Mercado Pago; no se pudo confirmar contra un
# aviso real. Si la respuesta no tiene la forma esperada, no se aplica nada.

COBROS: dict = {}
_LEER_COBRO_REAL = []


@pytest.fixture(autouse=True)
def _cobros(monkeypatch):
    import proyecto_maria.main as main_mod
    COBROS.clear()
    if not _LEER_COBRO_REAL:
        _LEER_COBRO_REAL.append(getattr(main_mod, "_leer_cobro_autorizado_mp", None))

    def _leer(cobro_id):
        if cobro_id not in COBROS:
            raise main_mod._MPIlegible(cobro_id)
        return COBROS[cobro_id]
    monkeypatch.setattr(main_mod, "_leer_cobro_autorizado_mp", _leer, raising=False)


def _renovacion(usuario: str, monto: float = 30000.0, estado_pago: str = "approved", sufijo: str = "1"):
    """Una renovación: la suscripción, el cobro autorizado y su pago. El pago
    de una renovación no siempre trae la referencia: la tiene la suscripción."""
    pre = f"pre-{usuario}"
    SUSCRIPCIONES[pre] = {"id": pre, "status": "authorized", "external_reference": f"{usuario}:premium",
                          "auto_recurring": {"transaction_amount": 30000.0, "currency_id": "ARS"}}
    pid = f"prn{sufijo}-{usuario}"
    PAGOS[pid] = {"id": pid, "status": estado_pago, "external_reference": "", "transaction_amount": monto,
                  "currency_id": "ARS", "payer": {"id": "payer-1"},
                  "date_approved": datetime.now(timezone.utc).isoformat()}
    cobro = f"cob{sufijo}-{usuario}"
    COBROS[cobro] = {"id": cobro, "preapproval_id": pre, "type": "scheduled", "status": "processed",
                     "transaction_amount": monto, "currency_id": "ARS",
                     "payment": {"id": pid, "status": estado_pago, "status_detail": "accredited"}}
    return cobro, pid


def _aviso_cobro(client, cobro: str):
    client.cookies.clear()
    return client.post("/api/payments/webhook",
                       **aviso_firmado("subscription_authorized_payment", cobro, "secreto-de-prueba"))


def test_una_renovacion_extiende_el_periodo_una_sola_vez(client):
    usuario = _unique("mp4_ren")
    _register(client, usuario)
    fin_actual = datetime.now(timezone.utc) + timedelta(days=2)
    _set_user(usuario, billing_status="active", plan="premium", trial_ends_at=fin_actual)
    cobro, pid = _renovacion(usuario)
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text
    nuevo = _fin(_get_user(usuario))
    assert abs((nuevo - (fin_actual + timedelta(days=30))).total_seconds()) < 120, nuevo
    assert _leer_pago(pid)["estado"] == "aplicado"
    # el mismo cobro otra vez, y su pago avisado como pago: no suma de nuevo
    PAGOS[pid]["metadata"] = {"preapproval_id": f"pre-{usuario}"}
    PAGOS[pid]["external_reference"] = f"{usuario}:premium"
    for r in (_aviso_cobro(client, cobro), _aviso_pago(client, pid)):
        assert r.status_code == 200, r.text
    assert abs((_fin(_get_user(usuario)) - nuevo).total_seconds()) < 1


def test_una_renovacion_vuelve_a_activar_una_cuenta_vencida(client):
    usuario = _unique("mp4_venc")
    _register(client, usuario)
    _vencida(usuario)
    cobro, _ = _renovacion(usuario)
    assert _aviso_cobro(client, cobro).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"


def test_una_renovacion_de_menos_queda_rechazada(client):
    usuario = _unique("mp4_menos")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario, monto=1000.0)
    assert _aviso_cobro(client, cobro).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid)["estado"] == "rechazado"


def test_un_cobro_no_aprobado_no_hace_nada(client):
    usuario = _unique("mp4_rech")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario, estado_pago="rejected")
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200 and "rejected" in r.json().get("skipped", ""), r.text
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid) == {}


@pytest.mark.parametrize("estado_en_el_cobro", [None, "in_process"], ids=["sin_estado", "pendiente"])
def test_lo_que_decide_es_el_estado_del_pago_y_no_el_que_copia_el_cobro(client, estado_en_el_cobro):
    """El cobro trae una copia del estado del pago y su forma no se confirmó
    contra un aviso real (D30): si falta o quedó vieja y el pago está
    aprobado, la renovación se cobró y se aplica."""
    usuario = _unique("mp4_estado")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    if estado_en_el_cobro is None:
        COBROS[cobro]["payment"].pop("status")
    else:
        COBROS[cobro]["payment"]["status"] = estado_en_el_cobro
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text
    assert _get_user(usuario)["billing_status"] == "active"
    assert _leer_pago(pid)["estado"] == "aplicado"


def test_si_mercado_pago_no_contesta_el_cobro_reintenta(client):
    usuario = _unique("mp4_503")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    COBROS.clear()
    assert _aviso_cobro(client, cobro).status_code == 503
    assert _leer_pago(pid) == {}


def test_leer_un_cobro_no_arma_una_ruta_con_lo_que_mande_cualquiera(monkeypatch):
    """El id del cobro llega en un aviso sin firma: no puede cambiar la ruta
    que se le pide a Mercado Pago."""
    import proyecto_maria.main as main_mod
    pedidos = []

    class _Cliente:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, **k):
            pedidos.append(url)
            raise AssertionError("no tendría que pedir nada")

    monkeypatch.setattr(main_mod.httpx, "Client", _Cliente)
    funcion = _LEER_COBRO_REAL[0]
    for malo in ("../v1/payments/1", "1?x=2", "1/2", "", "a" * 80):
        with pytest.raises(ValueError):
            funcion(malo)
    assert pedidos == []


def test_una_renovacion_con_el_id_de_pago_numerico_se_aplica(client):
    """Mercado Pago manda los ids de pago como números."""
    import time
    usuario = _unique("mp4_num")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    numero = time.time_ns()
    PAGOS[str(numero)] = {**PAGOS.pop(pid), "id": numero}
    COBROS[cobro]["payment"]["id"] = numero
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text
    assert _get_user(usuario)["billing_status"] == "active"
    assert _leer_pago(str(numero))["estado"] == "aplicado"


def test_si_no_se_puede_leer_la_suscripcion_de_una_renovacion_reintenta(client):
    usuario = _unique("mp4_susf")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    SUSCRIPCIONES.clear()
    assert _aviso_cobro(client, cobro).status_code == 503
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"


def test_una_renovacion_cuyo_pago_dice_otra_cuenta_no_se_aplica(client):
    """La suscripción del cobro es de una cuenta y el pago dice otra: no se
    aplica a ninguna de las dos y queda rechazado."""
    usuario = _unique("mp4_otra")
    otro = _unique("mp4_otro")
    for u in (usuario, otro):
        _register(client, u)
        _vencida(u)
    cobro, pid = _renovacion(usuario)
    PAGOS[pid]["external_reference"] = f"{otro}:premium"
    assert _aviso_cobro(client, cobro).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _get_user(otro)["billing_status"] == "past_due"
    fila = _leer_pago(pid)
    assert fila["estado"] == "rechazado" and "otra cuenta" in fila["motivo"], fila


def _httpx_simulado(monkeypatch, responder):
    """httpx de main con un transporte simulado: el TestClient sigue usando el
    httpx de verdad."""
    import types
    import httpx
    import proyecto_maria.main as main_mod
    pedidos = []

    def _handler(request):
        pedidos.append(request)
        return responder(request)

    def _cliente(**kw):
        return httpx.Client(transport=httpx.MockTransport(_handler), **kw)
    monkeypatch.setattr(main_mod, "httpx", types.SimpleNamespace(Client=_cliente, HTTPError=httpx.HTTPError))
    monkeypatch.setattr(main_mod, "_leer_cobro_autorizado_mp", _LEER_COBRO_REAL[0])
    return pedidos


def test_leer_un_cobro_pide_su_ruta_con_el_token(monkeypatch):
    import httpx
    import proyecto_maria.main as main_mod
    pedidos = _httpx_simulado(monkeypatch, lambda r: httpx.Response(200, json={"id": "cob-1"}))
    assert main_mod._leer_cobro_autorizado_mp("cob-1") == {"id": "cob-1"}
    assert [str(p.url) for p in pedidos] == ["https://api.mercadopago.com/authorized_payments/cob-1"]
    assert pedidos[0].headers["authorization"] == "Bearer TEST-fake"


def _contesta_500(request):
    """Un 500 con el cobro bueno en el cuerpo: si no se mirara el estado, se
    aplicaría."""
    import httpx
    return httpx.Response(500, json=COBROS[request.url.path.rsplit("/", 1)[-1]])


def _sin_conexion(request):
    import httpx
    raise httpx.ConnectError("simulado: sin conexión", request=request)


def _contesta_html(request):
    import httpx
    return httpx.Response(200, content=b"<html>no</html>")


@pytest.mark.parametrize("responder, esperado", [
    (_contesta_500, 503), (_sin_conexion, 503), (_contesta_html, 503),
], ids=["http_500", "sin_conexion", "no_es_json"])
def test_el_cobro_que_mercado_pago_no_contesta_bien_no_aplica_nada(client, monkeypatch, responder, esperado):
    """De punta a punta con la lectura real: 500, sin conexión o una respuesta
    que no es JSON → 503 para que Mercado Pago reintente (vuelta 2, b)."""
    usuario = _unique("mp4_http")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    pedidos = _httpx_simulado(monkeypatch, responder)
    r = _aviso_cobro(client, cobro)
    assert r.status_code == esperado, r.text
    assert len(pedidos) == 1
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid) == {}


# ── El id del pago es el que dice Mercado Pago ───────────────────────
# Mercado Pago lee el id del pago de la ruta que se le pide: «9000001#a»,
# «%39000001», «./9000001» o «09000001» son el mismo pago. El registro de
# pagos aplicados no puede tomarlos por pagos distintos. Este simulado
# resuelve el id como lo haría la ruta de su API.

PEDIDOS: list = []


def _como_mp(pid) -> str:
    import posixpath
    from urllib.parse import unquote
    ruta = str(pid).split("#")[0].split("?")[0]
    return posixpath.normpath("/v1/payments/" + unquote(ruta)).rsplit("/", 1)[-1].lstrip("0")


class _PagosComoMP:
    def get(self, pid):
        PEDIDOS.append(str(pid))
        pago = PAGOS.get(_como_mp(pid))
        if pago is None:
            return {"status": 404, "response": {"message": "Payment not found"}}
        return {"status": 200, "response": pago}


class _SDKComoMP(_SDK):
    def payment(self):
        return _PagosComoMP()


@pytest.fixture
def mp_como_mp(monkeypatch):
    import proyecto_maria.main as main_mod
    PEDIDOS.clear()
    monkeypatch.setattr(main_mod.mercadopago, "SDK", _SDKComoMP)


def _pago_numerico(referencia: str, monto: float = 45000.0) -> str:
    """Un pago con id numérico, que Mercado Pago devuelve como número."""
    import random
    pid = str(random.randint(10**9, 10**10 - 1))
    _pago(pid, referencia, monto)
    PAGOS[pid]["id"] = int(pid)
    return pid


VARIANTES = {
    "fragmento": lambda p: f"{p}#a",
    "consulta": lambda p: f"{p}?a=1",
    "escapado": lambda p: "%{:02X}{}".format(ord(p[0]), p[1:]),
    "punto": lambda p: f"./{p}",
    "cero": lambda p: f"0{p}",
}


@pytest.mark.parametrize("variante", sorted(VARIANTES))
def test_el_mismo_pago_escrito_de_otra_forma_no_se_aplica_otra_vez(client, mp_como_mp, variante):
    """Con un solo pago de plan y una recarga, reenviar sus ids escritos de
    otra forma daba un año de plan y cuarenta operaciones."""
    usuario = _unique("mp1_var")
    _register(client, usuario)
    plan = _pago_numerico(f"{usuario}:premium")
    recarga = _pago_numerico(f"{usuario}:topup", monto=10000.0)
    for pid in (plan, recarga):
        assert _aviso_pago(client, pid).status_code == 200
    antes = _get_user(usuario)
    for pid in (plan, recarga):
        r = _aviso_pago(client, VARIANTES[variante](pid))
        assert r.status_code < 500, r.text[:300]
    despues = _get_user(usuario)
    assert _fin(despues) == _fin(antes), (antes["trial_ends_at"], despues["trial_ends_at"])
    assert despues["extra_ops_remaining"] == antes["extra_ops_remaining"], despues


def test_un_id_con_barras_no_llega_a_mercado_pago(client, mp_como_mp):
    """El aviso IPN no viene firmado: su id no puede cambiar la ruta que se
    le pide a Mercado Pago (llegaba a /preapproval/ABC)."""
    r = _aviso_pago(client, "../../preapproval/ABC")
    assert r.status_code == 400, r.text[:300]
    assert PEDIDOS == []


@pytest.mark.parametrize("cuenta", ["usuario", "organizacion"])
def test_el_ultimo_pago_de_antes_del_registro_no_se_aplica_otra_vez(client, cuenta):
    """Antes de COBRO-MP-1 sólo se guardaba el último pago de cada cuenta:
    al desplegar, ese pago no tiene fila en el registro de pagos aplicados."""
    usuario = _unique("mp1_ult")
    _register(client, usuario)
    fin = datetime.now(timezone.utc) + timedelta(days=25)
    pid = f"pl-{usuario}"
    if cuenta == "usuario":
        _set_user(usuario, billing_status="active", plan="premium", trial_ends_at=fin, last_payment_id=pid)
        _pago(pid, f"{usuario}:premium")
        leer = lambda: _get_user(usuario)  # noqa: E731
    else:
        org_id = _org(usuario, billing_status="active", plan="premium", trial_ends_at=fin, last_payment_id=pid)
        _pago(pid, f"org:{org_id}:premium")
        leer = lambda: _leer_org(org_id)  # noqa: E731
    assert _aviso_pago(client, pid).status_code == 200
    assert abs((_fin(leer()) - fin).total_seconds()) < 2, leer()


# COBRO-MP-1, A: el registro de pagos empezó con el despliegue. Un pago que el
# código viejo ya aplicó no tiene fila; si no es el último de la cuenta,
# last_payment_id tampoco lo frena y el aviso IPN sin firma lo volvía a aplicar.
APROBADO_ANTES_DEL_REGISTRO = "2020-03-01T10:00:00.000-03:00"


@pytest.mark.parametrize("cuenta", ["usuario", "organizacion"])
def test_un_pago_viejo_que_no_es_el_ultimo_no_se_aplica_otra_vez(client, cuenta):
    """El código viejo aplicó dos pagos y sólo recuerda el último: reenviar el
    anterior no renueva la cuenta vencida ni la reactiva."""
    usuario = _unique("mp1_ant")
    _register(client, usuario)
    vencida = datetime.now(timezone.utc) - timedelta(days=40)
    viejo, ultimo = f"pv1-{usuario}", f"pv2-{usuario}"
    if cuenta == "usuario":
        _set_user(usuario, billing_status="past_due", plan="premium", trial_ends_at=vencida,
                  last_payment_id=ultimo)
        ref = f"{usuario}:premium"
        leer = lambda: _get_user(usuario)  # noqa: E731
    else:
        org_id = _org(usuario, billing_status="past_due", plan="premium", trial_ends_at=vencida,
                      last_payment_id=ultimo)
        ref = f"org:{org_id}:premium"
        leer = lambda: _leer_org(org_id)  # noqa: E731
    for pid in (viejo, ultimo):
        _pago(pid, ref)
        PAGOS[pid]["date_approved"] = APROBADO_ANTES_DEL_REGISTRO
    for pid in (viejo, ultimo, viejo):
        r = _aviso_pago(client, pid)
        assert r.status_code == 200, r.text[:300]
    despues = leer()
    assert despues["billing_status"] == "past_due", f"un pago viejo reenviado se volvió a aplicar: {despues}"
    assert abs((_fin(despues) - vencida).total_seconds()) < 2, f"un pago viejo reenviado se volvió a aplicar: {despues}"
    assert _leer_pago(viejo).get("estado") != "aplicado", _leer_pago(viejo)


def test_un_pago_viejo_queda_a_la_vista_del_admin(client):
    """No se aplica, pero queda rechazado con su motivo: si fuera un pago
    legítimo que llegó tarde, Emi lo ve en los pagos rechazados."""
    usuario = _unique("mp1_vis")
    _register(client, usuario)
    pid = _pago(f"pvis-{usuario}", f"{usuario}:premium")
    PAGOS[pid]["date_approved"] = APROBADO_ANTES_DEL_REGISTRO
    assert _aviso_pago(client, pid).status_code == 200
    fila = _leer_pago(pid)
    assert fila.get("estado") == "rechazado", f"el pago viejo no quedó a la vista: {fila}"
    assert "antes de que empezara el registro" in (fila.get("motivo") or ""), fila


@pytest.mark.parametrize("fecha", [None, "", "ayer", "sin_zona"],
                         ids=["sin_fecha", "vacia", "ilegible", "sin_zona"])
def test_un_pago_sin_fecha_de_aprobacion_legible_no_se_aplica(client, fecha):
    """Sin la fecha no se sabe si es anterior al registro: no se aplica."""
    usuario = _unique("mp1_fec")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pf-{usuario}", f"{usuario}:premium")
    if fecha is None:
        PAGOS[pid].pop("date_approved", None)
    elif fecha == "sin_zona":
        # de ahora: sin zona, no la frena el corte del registro sino la zona
        PAGOS[pid]["date_approved"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    else:
        PAGOS[pid]["date_approved"] = fecha
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due", "se aplicó un pago sin fecha de aprobación legible"
    fila = _leer_pago(pid)
    assert (fila.get("estado"), fila.get("motivo")) == ("rechazado", "sin fecha de aprobación legible"), fila


def test_un_pago_nuevo_se_aplica(client):
    """El corte no frena lo que se aprobó después de empezar el registro."""
    usuario = _unique("mp1_nue")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pn-{usuario}", f"{usuario}:premium")
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"


def test_sin_token_el_aviso_de_una_renovacion_no_se_pierde(client, monkeypatch):
    """Sin MP_ACCESS_TOKEN no se puede leer el cobro: el aviso no se da por
    procesado, para que Mercado Pago lo reintente."""
    import proyecto_maria.main as main_mod
    usuario = _unique("mp1_tok")
    _register(client, usuario)
    cobro, pid = _renovacion(usuario)
    monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "")
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 400, r.text[:300]
    assert _leer_pago(pid) == {}


def _base_temporal(tmp_path):
    from sqlalchemy import create_engine
    from proyecto_maria.database.models import Base, InicioRegistroPagosMP, PagoMercadoPagoAplicado
    motor = create_engine(f"sqlite:///{tmp_path / 'inicio.db'}")
    Base.metadata.create_all(motor, tables=[PagoMercadoPagoAplicado.__table__, InicioRegistroPagosMP.__table__])
    return motor


def _leer_inicio(motor):
    from sqlalchemy import text
    with motor.connect() as conn:
        filas = conn.execute(text("SELECT id, desde FROM mp_registro_pagos_inicio")).all()
    return [(i, datetime.fromisoformat(str(d)).replace(tzinfo=None)) for i, d in filas]


def test_el_inicio_del_registro_es_el_primer_pago_registrado_y_no_se_mueve(tmp_path):
    """Si COBRO-MP-1 ya estaba desplegado, el registro empezó con su primer
    pago, no con este arranque: un pago aplicado entre medio sigue frenado
    por su fila, y uno de antes, por el corte."""
    from sqlalchemy import text
    from proyecto_maria.database.connection import sembrar_inicio_registro_mp
    motor = _base_temporal(tmp_path)
    with motor.begin() as conn:
        for pid, cuando in (("b", "2026-10-20 12:00:00"), ("a", "2026-10-15 09:30:00")):
            conn.execute(text("INSERT INTO mp_pagos_aplicados (payment_id, cuenta, tipo, estado, aplicado_en)"
                              " VALUES (:p, 'x', 'premium', 'aplicado', :c)"), {"p": pid, "c": cuando})
    with motor.begin() as conn:
        sembrar_inicio_registro_mp(conn)
    assert _leer_inicio(motor) == [(1, datetime(2026, 10, 15, 9, 30))], _leer_inicio(motor)
    with motor.begin() as conn:
        conn.execute(text("DELETE FROM mp_pagos_aplicados"))
    with motor.begin() as conn:
        sembrar_inicio_registro_mp(conn)
    assert _leer_inicio(motor) == [(1, datetime(2026, 10, 15, 9, 30))], "el inicio del registro se movió al rearrancar"


def test_sin_pagos_registrados_el_inicio_es_ahora(tmp_path):
    from proyecto_maria.database.connection import sembrar_inicio_registro_mp
    motor = _base_temporal(tmp_path)
    antes = datetime.now(timezone.utc).replace(tzinfo=None)
    with motor.begin() as conn:
        sembrar_inicio_registro_mp(conn)
    [(_, desde)] = _leer_inicio(motor)
    assert abs((desde - antes).total_seconds()) < 5, desde
