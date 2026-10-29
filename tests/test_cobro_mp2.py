"""COBRO-MP-2: cancelar, una sola suscripción y reactivar pagando.

AUDITORIA-2026-10-06 C2, C4 y C8, con la D7 de la PM (2026-10-28):
- Cancelar en CDI cancela también la suscripción en Mercado Pago; la cuenta
  sigue hasta el fin del período. Si Mercado Pago no contesta, no se cancela
  a medias.
- El checkout no deja pagar dos veces una suscripción vigente; si la cuenta
  no está vigente, la vieja se cancela antes de crear la nueva.
- Un pago suma desde el fin del período también en la prueba y en la
  cancelada (D7.1 a).
- Reactivar una prueba no la activa; reactivar algo pagado lleva al checkout
  (D7.3 a).
- Sin token, fuera de desarrollo y pruebas, no hay demo; la demo no dice
  «activada» ni cambia la cuenta (D7.4 a).

Mercado Pago simulado: ni el SDK real ni internet.
"""
import asyncio
import json
import re
import types
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from sqlalchemy.future import select

from proyecto_maria.database.connection import get_async_session
from proyecto_maria.database.models import User
from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401

SUS: dict = {}        # id de la suscripción → estado en Mercado Pago
FALLA: dict = {}      # método HTTP → responder que falla
PEDIDOS: list = []    # lo que se le pidió a la API de Mercado Pago
CREADAS: list = []    # suscripciones y preferences creadas con el SDK
PAGOS: dict = {}

_RUTA_SUS = re.compile(r"https://api\.mercadopago\.com/preapproval/([^/?]+)")


def _api_mp(request):
    PEDIDOS.append(request)
    if request.method in FALLA:
        return FALLA[request.method](request)
    m = _RUTA_SUS.fullmatch(str(request.url))
    if not m or m.group(1) not in SUS:
        return httpx.Response(404, json={"message": "not found"})
    sid = m.group(1)
    if request.method == "PUT":
        if json.loads(request.content or b"{}") != {"status": "cancelled"}:
            return httpx.Response(400, json={"message": "cuerpo inesperado"})
        SUS[sid] = "cancelled"
    elif request.method != "GET":
        return httpx.Response(405, json={})
    return httpx.Response(200, json={"id": sid, "status": SUS[sid]})


def _contesta_500(request):
    return httpx.Response(500, json={})


def _sin_conexion(request):
    raise httpx.ConnectError("simulado: sin conexión", request=request)


class _Creador:
    def __init__(self, tipo):
        self.tipo = tipo

    def create(self, datos):
        nuevo = f"nueva-{len(CREADAS) + 1}"
        CREADAS.append((self.tipo, datos))
        if self.tipo == "preapproval":
            SUS[nuevo] = "pending"
        return {"status": 201, "response": {"id": nuevo, "init_point": f"https://mp.example/{nuevo}"}}


class _Pagos:
    def get(self, pid):
        return {"status": 200, "response": PAGOS[str(pid)]}


class _SDK:
    def __init__(self, token):
        pass

    def preapproval(self):
        return _Creador("preapproval")

    def preference(self):
        return _Creador("preference")

    def payment(self):
        return _Pagos()


@pytest.fixture(autouse=True)
def _mp(monkeypatch):
    import proyecto_maria.main as main_mod
    for d in (SUS, FALLA, PAGOS):
        d.clear()
    PEDIDOS.clear()
    CREADAS.clear()
    monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", "secreto-de-prueba")
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
    monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setenv("MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setenv("MP_PREAPPROVAL_PLAN_ID_PREMIUM", "plan-premium")
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setattr(main_mod.mercadopago, "SDK", _SDK)
    # httpx de main con la API simulada: el TestClient sigue con el de verdad.
    simulado = types.SimpleNamespace(**{k: getattr(httpx, k) for k in dir(httpx) if not k.startswith("_")})
    simulado.Client = lambda **kw: httpx.Client(transport=httpx.MockTransport(_api_mp), **kw)
    monkeypatch.setattr(main_mod, "httpx", simulado)


def _sin_token(monkeypatch):
    import proyecto_maria.main as main_mod
    monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "")
    monkeypatch.delenv("MP_ACCESS_TOKEN", raising=False)


def _fin(usuario: dict) -> datetime:
    fin = usuario["trial_ends_at"]
    if isinstance(fin, str):
        fin = datetime.fromisoformat(fin)
    return fin if fin.tzinfo else fin.replace(tzinfo=timezone.utc)


def _leer(username: str) -> dict:
    async def _run():
        async for db in get_async_session():
            u = (await db.execute(select(User).where(User.username == username))).scalars().first()
            return {"billing_status": u.billing_status, "trial_ends_at": u.trial_ends_at,
                    "mp_preapproval_id": u.mp_preapproval_id}
    return asyncio.new_event_loop().run_until_complete(_run())


def _suscripto(client, prefijo, estado_mp="authorized", billing_status="active", dias=20):
    """Una cuenta que pagó con Mercado Pago, con su suscripción en MP."""
    usuario = _unique(prefijo)
    _register(client, usuario)
    sid = f"sus-{usuario}"
    SUS[sid] = estado_mp
    _set_user(usuario, billing_status=billing_status, plan="premium", payment_provider="mercadopago",
              trial_ends_at=datetime.now(timezone.utc) + timedelta(days=dias), mp_preapproval_id=sid)
    return usuario, sid


def _cerca(a: datetime, b: datetime) -> bool:
    return abs(a - b) < timedelta(minutes=5)


# --- Cancelar (C2) ---

def test_cancelar_cancela_la_suscripcion_en_mp_y_sigue_hasta_el_fin(client):
    usuario, sid = _suscripto(client, "mp2_can")
    fin = _fin(_leer(usuario))
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, r.text
    puts = [p for p in PEDIDOS if p.method == "PUT"]
    assert [str(p.url) for p in puts] == [f"https://api.mercadopago.com/preapproval/{sid}"], PEDIDOS
    assert json.loads(puts[0].content) == {"status": "cancelled"}
    assert puts[0].headers["authorization"] == "Bearer TEST-fake"
    assert SUS[sid] == "cancelled"
    despues = _leer(usuario)
    assert despues["billing_status"] == "canceled"
    assert _cerca(_fin(despues), fin), despues
    assert r.json()["service_until"]


@pytest.mark.parametrize("responder", [_contesta_500, _sin_conexion], ids=["http_500", "sin_conexion"])
def test_si_mp_no_cancela_no_se_cancela_a_medias(client, responder):
    usuario, sid = _suscripto(client, "mp2_canfalla")
    FALLA["PUT"] = responder
    FALLA["GET"] = responder
    r = client.post("/api/billing/cancel")
    assert r.status_code in (502, 503), r.text
    assert "No se pudo cancelar" in r.json()["detail"], r.json()
    assert len(PEDIDOS) >= 1
    despues = _leer(usuario)
    assert despues["billing_status"] == "active", despues
    assert despues["mp_preapproval_id"] == sid
    assert SUS[sid] == "authorized"


def test_si_mp_ya_la_tenia_cancelada_cancelar_sigue(client):
    """El PUT da error pero la suscripción ya figura cancelada: está hecho."""
    usuario, sid = _suscripto(client, "mp2_canya", estado_mp="cancelled")
    FALLA["PUT"] = _contesta_500
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, r.text
    assert [p.method for p in PEDIDOS] == ["PUT", "GET"]
    assert _leer(usuario)["billing_status"] == "canceled"


def test_sin_token_no_cancela_una_suscripcion_a_medias(client, monkeypatch):
    usuario, sid = _suscripto(client, "mp2_cantok")
    _sin_token(monkeypatch)
    r = client.post("/api/billing/cancel")
    assert r.status_code == 503, r.text
    assert PEDIDOS == []
    assert _leer(usuario)["billing_status"] == "active"


def test_cancelar_sin_suscripcion_no_llama_a_mp(client):
    """Guarda (no es rojo antes): la prueba sin suscripción se cancela sólo en CDI."""
    usuario = _unique("mp2_cantrial")
    _register(client, usuario)
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, r.text
    assert PEDIDOS == []
    assert _leer(usuario)["billing_status"] == "canceled"


# --- Reactivar (C8, D7.3) ---

def test_cancelar_y_reactivar_una_prueba_no_la_activa(client):
    usuario = _unique("mp2_reprueba")
    _register(client, usuario)
    fin = _fin(_leer(usuario))
    assert client.post("/api/billing/cancel").status_code == 200
    r = client.post("/api/billing/reactivate")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["billing_status"] == "trial", cuerpo
    assert cuerpo["needs_checkout"] is False
    despues = _leer(usuario)
    assert despues["billing_status"] == "trial", despues
    assert _cerca(_fin(despues), fin)
    assert "próximo cobro" not in json.dumps(cuerpo, ensure_ascii=False).lower()


def test_reactivar_lo_pagado_lleva_al_checkout_y_dice_que_cobra_ahora(client):
    usuario, sid = _suscripto(client, "mp2_repago")
    assert client.post("/api/billing/cancel").status_code == 200
    fin = _fin(_leer(usuario))
    r = client.post("/api/billing/reactivate")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["needs_checkout"] is True, cuerpo
    assert cuerpo["billing_status"] == "canceled", cuerpo
    mensaje = cuerpo["message"]
    assert "ahora" in mensaje and "30 días" in mensaje, mensaje
    assert fin.strftime("%d/%m/%Y") in mensaje, mensaje
    assert _leer(usuario)["billing_status"] == "canceled"


# --- Una sola suscripción (C4, D7.2) ---

def test_el_segundo_checkout_con_una_vigente_se_frena(client):
    usuario, sid = _suscripto(client, "mp2_dos")
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 409, r.text
    assert "Ya tenés una suscripción" in r.json()["detail"], r.json()
    assert CREADAS == []
    assert SUS[sid] == "authorized"
    assert _leer(usuario)["mp_preapproval_id"] == sid


@pytest.mark.parametrize("estado_mp, billing_status, dias, cancela", [
    ("pending", "active", 20, True),
    ("paused", "past_due", -10, True),
    ("cancelled", "past_due", -10, False),
], ids=["pending", "pausada", "ya_cancelada"])
def test_sin_cuenta_vigente_la_vieja_se_cancela_antes_de_crear(client, estado_mp, billing_status, dias, cancela):
    usuario, sid = _suscripto(client, "mp2_vieja", estado_mp=estado_mp,
                              billing_status=billing_status, dias=dias)
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 200, r.text
    assert [str(p.url) for p in PEDIDOS if p.method == "PUT"] == (
        [f"https://api.mercadopago.com/preapproval/{sid}"] if cancela else []), PEDIDOS
    assert SUS[sid] == "cancelled"
    assert [t for t, _ in CREADAS] == ["preapproval"]
    assert _leer(usuario)["mp_preapproval_id"] == r.json()["preapproval_id"] != sid


@pytest.mark.parametrize("falla", ["PUT_500", "PUT_sin_conexion"])
def test_si_no_se_puede_cancelar_la_vieja_no_se_crea_nada(client, falla):
    usuario, sid = _suscripto(client, "mp2_viejafalla", estado_mp="pending", billing_status="past_due", dias=-10)
    FALLA["PUT"] = _contesta_500 if falla == "PUT_500" else _sin_conexion
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 503, r.text
    assert CREADAS == []
    assert SUS[sid] == "pending"
    assert _leer(usuario)["mp_preapproval_id"] == sid


def _estado_raro(request):
    return httpx.Response(200, json={"id": "x", "status": "otro"})


@pytest.mark.parametrize("responder", [_contesta_500, _sin_conexion, _estado_raro],
                         ids=["http_500", "sin_conexion", "estado_desconocido"])
def test_si_no_se_sabe_como_esta_la_suscripcion_no_se_crea_otra(client, responder):
    usuario, sid = _suscripto(client, "mp2_get")
    FALLA["GET"] = responder
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 503, r.text
    assert CREADAS == []
    assert [p.method for p in PEDIDOS] == ["GET"]


def test_modo_preference_con_suscripcion_vigente_tambien_se_frena(client, monkeypatch):
    monkeypatch.delenv("MP_PREAPPROVAL_PLAN_ID_PREMIUM", raising=False)
    _suscripto(client, "mp2_pref")
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 409, r.text
    assert CREADAS == []


# --- Un pago no acorta el período (D7.1 a, D7.2 preference) ---

def _pago(pid: str, referencia: str, monto: float = 45000.0) -> str:
    PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": referencia,
                  "transaction_amount": monto, "currency_id": "ARS", "payer": {"id": "payer-1"},
                  "date_approved": datetime.now(timezone.utc).isoformat()}
    return pid


def _aviso_ipn(client, pid: str):
    client.cookies.clear()
    return client.post(f"/api/payments/webhook?topic=payment&id={pid}")


@pytest.mark.parametrize("estado, proveedor", [
    ("trial", None), ("canceled", "mercadopago"), ("canceled", None),
], ids=["prueba", "cancelada_pagada", "prueba_cancelada"])
def test_un_pago_suma_desde_el_fin_del_periodo(client, estado, proveedor):
    usuario = _unique("mp2_pago")
    _register(client, usuario)
    fin = datetime.now(timezone.utc) + timedelta(days=10)
    _set_user(usuario, billing_status=estado, trial_ends_at=fin, payment_provider=proveedor)
    pid = _pago(f"pp-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    despues = _get_user(usuario)
    assert despues["billing_status"] == "active", despues
    assert _cerca(_fin(despues), fin + timedelta(days=30)), (_fin(despues), fin)


# --- Sin token (D7.4 a) ---

@pytest.mark.parametrize("entorno", ["production", None, "staging"], ids=["produccion", "sin_variable", "otro"])
def test_sin_token_fuera_de_desarrollo_no_hay_demo(client, monkeypatch, entorno):
    import proyecto_maria.main as main_mod
    usuario = _unique("mp2_prod")
    _register(client, usuario)
    _sin_token(monkeypatch)
    if entorno is None:
        monkeypatch.delenv("ENVIRONMENT", raising=False)
    else:
        monkeypatch.setenv("ENVIRONMENT", entorno)
    antes = dict(main_mod.pending_payments)
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 503, r.text
    assert "demo" not in r.text.lower()
    assert main_mod.pending_payments == antes

    main_mod.pending_payments["demo_prod0001"] = {"status": "pending", "username": usuario, "plan": "premium"}
    try:
        assert client.get("/api/payments/demo-checkout/demo_prod0001").status_code == 404
        assert client.post("/api/payments/demo-confirm/demo_prod0001").status_code == 404
        assert main_mod.pending_payments["demo_prod0001"]["status"] == "pending"
    finally:
        main_mod.pending_payments.pop("demo_prod0001", None)
    assert _leer(usuario)["billing_status"] == "trial"


def test_la_demo_no_dice_activada_ni_cambia_la_cuenta(client, monkeypatch):
    usuario = _unique("mp2_demo")
    _register(client, usuario)
    _sin_token(monkeypatch)
    antes = _leer(usuario)
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 200, r.text
    assert r.json()["mode"] == "demo"
    demo_id = r.json()["preference_id"]
    assert client.get(f"/api/payments/demo-checkout/{demo_id}").status_code == 200
    assert client.post(f"/api/payments/demo-confirm/{demo_id}").status_code == 200
    pagina = client.get(f"/api/payments/success?demo=true&preference_id={demo_id}")
    assert pagina.status_code == 200
    assert "activada" not in pagina.text.lower(), pagina.text[:600]
    assert "user_plan" not in pagina.text
    assert "prueba" in pagina.text.lower()
    assert _leer(usuario) == antes


def test_la_pagina_de_exito_sin_token_no_dice_activada(client, monkeypatch):
    _sin_token(monkeypatch)
    pagina = client.get("/api/payments/success")
    assert "activada" not in pagina.text.lower(), pagina.text[:600]
    assert "user_plan" not in pagina.text


# --- Etiqueta «Próximo cobro» (D7.3: ningún texto la dice si no lo hay) ---

# El id se guarda al abrir el checkout, antes de pagar: una cuenta activa sin
# un pago de Mercado Pago que abrió el checkout y no pagó no tiene próximo cobro.
@pytest.mark.parametrize("estado, con_suscripcion, proveedor, renueva", [
    ("active", True, "mercadopago", True), ("active", False, "mercadopago", False),
    ("active", True, None, False), ("canceled", True, "mercadopago", False), ("trial", False, None, False),
], ids=["suscripta", "sin_suscripcion", "checkout_sin_pagar", "cancelada", "prueba"])
def test_billing_me_dice_si_hay_proximo_cobro(client, estado, con_suscripcion, proveedor, renueva):
    usuario = _unique("mp2_me")
    _register(client, usuario)
    _set_user(usuario, billing_status=estado, payment_provider=proveedor,
              mp_preapproval_id=f"sus-{usuario}" if con_suscripcion else None)
    r = client.get("/api/billing/me")
    assert r.status_code == 200, r.text
    assert r.json().get("renueva") is renueva, r.json()
