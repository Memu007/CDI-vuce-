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
import threading
import time
import types
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import requests

from sqlalchemy.future import select

from proyecto_maria.database.connection import get_async_session
from proyecto_maria.database.models import User
from tests.mp_firma import aviso_firmado
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


def _contesta_sin_cancelar(request):
    sid = _RUTA_SUS.fullmatch(str(request.url)).group(1)
    return httpx.Response(200, json={"id": sid, "status": SUS[sid]})


class _Creador:
    def __init__(self, tipo):
        self.tipo = tipo

    def create(self, datos):
        if "create" in FALLA:
            return FALLA["create"](datos)
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
                    "mp_preapproval_id": u.mp_preapproval_id, "organization_id": u.organization_id}
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


@pytest.mark.parametrize("responder", [_contesta_500, _sin_conexion, _contesta_sin_cancelar],
                         ids=["http_500", "sin_conexion", "contesta_sin_cancelar"])
def test_si_mp_no_cancela_no_se_cancela_a_medias(client, responder):
    usuario, sid = _suscripto(client, "mp2_canfalla")
    FALLA["PUT"] = responder
    FALLA["GET"] = responder
    r = client.post("/api/billing/cancel")
    assert r.status_code in (502, 503), r.text
    assert "No se pudo confirmar la cancelación" in r.json()["detail"], r.json()
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
    assert [p.method for p in PEDIDOS] == ["GET", "PUT", "GET"]
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


def _estado_lista(request):
    return httpx.Response(200, json={"id": "x", "status": ["authorized"]})


@pytest.mark.parametrize("responder", [_contesta_500, _sin_conexion, _estado_raro, _estado_lista],
                         ids=["http_500", "sin_conexion", "estado_desconocido", "estado_lista"])
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


def _aviso_pago(client, pid: str):
    client.cookies.clear()
    return client.post("/api/payments/webhook", **aviso_firmado("payment", pid, "secreto-de-prueba"))


@pytest.mark.parametrize("estado, proveedor", [
    ("trial", None), ("canceled", "mercadopago"), ("canceled", None),
], ids=["prueba", "cancelada_pagada", "prueba_cancelada"])
def test_un_pago_suma_desde_el_fin_del_periodo(client, estado, proveedor):
    usuario = _unique("mp2_pago")
    _register(client, usuario)
    fin = datetime.now(timezone.utc) + timedelta(days=10)
    _set_user(usuario, billing_status=estado, trial_ends_at=fin, payment_provider=proveedor)
    pid = _pago(f"pp-{usuario}", f"{usuario}:premium")
    assert _aviso_pago(client, pid).status_code == 200
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


# --- Una sola suscripción por organización ---

@pytest.mark.parametrize("estado_mp, org_status, dias, codigo", [
    ("authorized", "active", 20, 409),
    ("authorized", "past_due", -10, 409),
    ("pending", "active", 20, 200),
    ("paused", "past_due", -10, 409),
], ids=["autorizada_vigente", "autorizada_vencida", "pending", "pausada"])
def test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org(client, estado_mp, org_status, dias, codigo):
    from tests.test_cobro_mp1 import _org
    primero, sid = _suscripto(client, "mp2_orgA", estado_mp=estado_mp)
    org_id = _org(primero, billing_status=org_status, plan="premium",
                  trial_ends_at=datetime.now(timezone.utc) + timedelta(days=dias))
    _set_user(primero, organization_id=org_id)
    segundo = _unique("mp2_orgB")
    _register(client, segundo)
    _set_user(segundo, organization_id=org_id)
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == codigo, r.text
    if codigo == 409:
        assert CREADAS == [] and SUS[sid] == estado_mp
        assert _leer(primero)["mp_preapproval_id"] == sid
        assert primero in r.json()["detail"], "el 409 dice quién la puede cancelar"
        assert "renueva sola" not in r.json()["detail"].lower()
    else:
        assert SUS[sid] == "cancelled" and [t for t, _ in CREADAS] == ["preapproval"]
        assert CREADAS[0][1]["external_reference"] == f"org:{org_id}:premium", "le cobra a la org"
        assert _leer(primero)["mp_preapproval_id"] is None
        assert _leer(segundo)["mp_preapproval_id"] == r.json()["preapproval_id"]


def _org_con_suscripcion(client, quien_entra: str):
    """Org activa: la dueña A y B, que abrió la suscripción; C, un miembro más.
    La sesión queda en quien_entra («duena», «abrio», «miembro» o «duena_de_otro»,
    dueña de otro estudio): se registra último."""
    from tests.test_cobro_mp1 import _org
    nombres = {k: _unique(f"mp2_{k}") for k in ("duena", "abrio", "miembro")}
    for k in sorted(nombres, key=lambda k: k == quien_entra):
        _register(client, nombres[k])
    sid = f"sus-{nombres['abrio']}"
    SUS[sid] = "authorized"
    fin = datetime.now(timezone.utc) + timedelta(days=20)
    # El pago de Mercado Pago se le aplica a la org (webhook, org_id).
    org_id = _org(nombres["duena"], billing_status="active", plan="premium", trial_ends_at=fin,
                  payment_provider="mercadopago")
    for k, u in nombres.items():
        _set_user(u, organization_id=org_id, billing_status="trial",
                  trial_ends_at=datetime.now(timezone.utc) + timedelta(days=3))
    _set_user(nombres["abrio"], mp_preapproval_id=sid)
    if quien_entra == "duena_de_otro":
        otra = _unique("mp2_otra")
        _register(client, otra)
        _set_user(otra, organization_id=_org(otra, billing_status="active", plan="premium", trial_ends_at=fin))
    return nombres, sid, org_id, fin


@pytest.mark.parametrize("quien, estado", [("duena", "authorized"), ("abrio", "authorized"), ("abrio", "paused")])
def test_en_una_org_cancelar_cancela_la_suscripcion_y_sigue_hasta_el_fin(client, quien, estado):
    from tests.test_cobro_mp1 import _leer_org
    nombres, sid, org_id, fin = _org_con_suscripcion(client, quien)
    SUS[sid] = estado
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, r.text
    assert SUS[sid] == "cancelled", "Mercado Pago sigue cobrando"
    org = _leer_org(org_id)
    assert org["billing_status"] == "canceled"
    assert _cerca(_fin(org), fin), "la org pierde días pagados"
    assert _cerca(_fin({"trial_ends_at": r.json()["service_until"]}), fin), r.json()
    assert _leer(nombres["abrio"])["mp_preapproval_id"] is None
    assert client.get("/api/billing/me").json()["billing_status"] == "canceled"


@pytest.mark.parametrize("tipo, queda", [("premium", "canceled"), ("topup", "trial")])
def test_en_una_org_reactivar_lo_pagado_lleva_al_checkout(client, tipo, queda):
    """Los pagos de la org se anotan como «org:<id>»: una recarga sola no es un plan."""
    from proyecto_maria.database.models import PagoMercadoPagoAplicado
    from tests.test_cobro_mp1 import _leer_org
    nombres, sid, org_id, fin = _org_con_suscripcion(client, "duena")

    async def _pago():
        async for db in get_async_session():
            db.add(PagoMercadoPagoAplicado(payment_id=_unique("pago"), cuenta=f"org:{org_id}", tipo=tipo))
            await db.commit()
            return
    asyncio.new_event_loop().run_until_complete(_pago())
    assert client.post("/api/billing/cancel").status_code == 200
    r = client.post("/api/billing/reactivate")
    assert r.status_code == 200, r.text
    assert r.json()["needs_checkout"] is (queda == "canceled") and r.json()["billing_status"] == queda, r.json()
    assert _leer_org(org_id)["billing_status"] == queda


def test_si_una_de_varias_no_se_cancela_la_cancelada_no_queda_anotada(client):
    """El checkout, con dos pendientes que cancela antes de crear: falla la segunda."""
    from tests.test_cobro_mp1 import _leer_org
    nombres, sid, otra, org_id = _dos_pendientes(client)
    cancela, falla = (nombres["abrio"], sid), (nombres["miembro"], otra)

    def _falla_una(request):
        s = _RUTA_SUS.fullmatch(str(request.url)).group(1)
        if s == falla[1] and request.method == "PUT":
            return httpx.Response(500, json={})
        if request.method == "PUT":
            SUS[s] = "cancelled"
        return httpx.Response(200, json={"id": s, "status": SUS[s]})
    FALLA["PUT"] = FALLA["GET"] = _falla_una
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 503, r.text
    assert _leer_org(org_id)["billing_status"] == "active" and CREADAS == []
    assert SUS[cancela[1]] == "cancelled" and _leer(cancela[0])["mp_preapproval_id"] is None
    assert SUS[falla[1]] != "cancelled" and _leer(falla[0])["mp_preapproval_id"] == falla[1]


# Quien cancela, y cuál falla: la pendiente de C, o la autorizada de B, que se ordena antes.
@pytest.mark.parametrize("quien, falla", [("duena", "pendiente"), ("abrio", "pendiente"), ("duena", "autorizada")])
def test_al_cancelar_la_que_paga_se_cancela_ultima(client, quien, falla):
    from tests.test_cobro_mp1 import _leer_org
    nombres, sid, org_id, _ = _org_con_suscripcion(client, quien)
    otra = f"sus-{nombres['miembro']}"
    SUS[otra] = "pending"
    _set_user(nombres["miembro"], mp_preapproval_id=otra)
    assert nombres["abrio"] < nombres["miembro"]
    no_cancela = otra if falla == "pendiente" else sid

    def _falla_una(request):
        s = _RUTA_SUS.fullmatch(str(request.url)).group(1)
        if request.method == "PUT":
            if s == no_cancela:
                return httpx.Response(500, json={})
            SUS[s] = "cancelled"
        return httpx.Response(200, json={"id": s, "status": SUS[s]})
    FALLA["PUT"] = FALLA["GET"] = _falla_una
    r = client.post("/api/billing/cancel")
    assert r.status_code == 503, r.text
    assert SUS[sid] == "authorized" and _leer(nombres["abrio"])["mp_preapproval_id"] == sid
    assert _leer_org(org_id)["billing_status"] == "active"
    # La pendiente que sí se canceló no queda anotada.
    queda = otra if falla == "pendiente" else None
    assert _leer(nombres["miembro"])["mp_preapproval_id"] == queda


def test_con_una_autorizada_de_otro_no_se_cancela_ninguna(client):
    # Se ordena antes que quien la abrió: si no se leen todas primero, se cancela.
    antes = _unique("mp2_a0")
    _register(client, antes)
    nombres, sid, org_id, _ = _org_con_suscripcion(client, "duena")
    assert antes < nombres["abrio"]
    SUS[f"sus-{antes}"] = "pending"
    _set_user(antes, organization_id=org_id, mp_preapproval_id=f"sus-{antes}")
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 409, r.text
    assert SUS == {sid: "authorized", f"sus-{antes}": "pending"} and CREADAS == []
    assert [p.method for p in PEDIDOS if p.method == "PUT"] == []
    assert _leer(antes)["mp_preapproval_id"] == f"sus-{antes}"


@pytest.mark.parametrize("abierta", [True, False], ids=["con_suscripcion", "sin_suscripcion"])
@pytest.mark.parametrize("quien", ["duena", "abrio", "miembro"])
def test_billing_me_muestra_la_suscripcion_del_estudio_a_todos(client, quien, abierta):
    nombres, sid, org_id, _ = _org_con_suscripcion(client, quien)
    if not abierta:
        _set_user(nombres["abrio"], mp_preapproval_id=None)
    yo = client.get("/api/billing/me").json()
    assert (yo["renueva"], yo["suscripcion_abierta"]) == (abierta, abierta), yo


# --- Quién toca la suscripción que paga el estudio ---

def _sin_cambios(nombres, sid, org_id):
    pass


def _cancelada_con_la_suya_anotada(nombres, sid, org_id):
    from tests.test_cobro_mp1 import _leer_org
    SUS[sid] = "paused"
    _leer_org(org_id, billing_status="canceled", payment_provider=None)


def _cancelada_por_la_duena(nombres, sid, org_id):
    from tests.test_cobro_mp1 import _leer_org
    SUS[sid] = "cancelled"
    _set_user(nombres["abrio"], mp_preapproval_id=None)
    _leer_org(org_id, billing_status="canceled", payment_provider=None)


def _pausada_y_vencida(nombres, sid, org_id):
    from tests.test_cobro_mp1 import _leer_org
    SUS[sid] = "paused"
    _leer_org(org_id, billing_status="past_due", trial_ends_at=datetime.now(timezone.utc) - timedelta(days=10))


def _del_miembro(estado, falla=None):
    def preparar(nombres, sid, org_id):
        SUS[f"sus-{nombres['miembro']}"] = estado
        _set_user(nombres["miembro"], mp_preapproval_id=f"sus-{nombres['miembro']}")
        if falla:
            FALLA["GET"] = FALLA["PUT"] = falla
    return preparar


def _la_que_paga(estado):
    def preparar(nombres, sid, org_id):
        SUS[sid] = estado
    return preparar


def _cancelo(nombres, sid, org_id):
    from tests.test_cobro_mp1 import _leer_org
    return SUS[sid] == "cancelled" and _leer_org(org_id)["billing_status"] == "canceled"


def _volvio_a_la_prueba(nombres, sid, org_id):
    from tests.test_cobro_mp1 import _leer_org
    return _leer_org(org_id)["billing_status"] == "trial"


def _abrio_otra(nombres, sid, org_id):
    return SUS[sid] == "cancelled" and [t for t, _ in CREADAS] == ["preapproval"]


def _salio_sin_suscripcion(cancelaciones):
    # El simulado acepta cancelar dos veces: se cuenta cuántas se le pidieron.
    def hecho(nombres, sid, org_id):
        suya, sale = f"sus-{nombres['miembro']}", _leer(nombres["miembro"])
        puts = [p for p in PEDIDOS if p.method == "PUT" and _RUTA_SUS.fullmatch(str(p.url)).group(1) == suya]
        return SUS[suya] == "cancelled" and sale["organization_id"] is None \
            and sale["mp_preapproval_id"] is None and len(puts) == cancelaciones
    return hecho


_SACAR_MIEMBRO = ("delete", "/api/organizations/members/{miembro}")
_SACAR_ABRIO = ("delete", "/api/organizations/members/{abrio}")
_SACA = {"duena": 200, "abrio": 403, "miembro": 403, "duena_de_otro": 404}
# Escenario → (preparar, pedido, lo que hace un 200, código según quién lo pide).
_QUIEN_TOCA = {
    "cancelar": (_sin_cambios, ("post", "/api/billing/cancel"), _cancelo,
                 {"duena": 200, "abrio": 200, "miembro": 403}),
    "reactivar": (_cancelada_por_la_duena, ("post", "/api/billing/reactivate"), _volvio_a_la_prueba,
                  {"duena": 200, "abrio": 403, "miembro": 403}),
    "reactivar_con_la_suya": (_cancelada_con_la_suya_anotada, ("post", "/api/billing/reactivate"),
                              _volvio_a_la_prueba, {"duena": 200, "abrio": 200, "miembro": 403}),
    "checkout_con_pausada": (_pausada_y_vencida, ("post", "/api/billing/checkout"), _abrio_otra,
                             {"duena": 409, "abrio": 200, "miembro": 409}),
    "sacar_con_pendiente": (_del_miembro("pending"), _SACAR_MIEMBRO, _salio_sin_suscripcion(1), _SACA),
    "sacar_con_cancelada": (_del_miembro("cancelled"), _SACAR_MIEMBRO, _salio_sin_suscripcion(0), _SACA),
    "sacar_sin_mp": (_del_miembro("pending", _contesta_500), _SACAR_MIEMBRO, None, {**_SACA, "duena": 503}),
    "sacar_a_la_que_paga": (_la_que_paga("authorized"), _SACAR_ABRIO, None, {**_SACA, "duena": 409}),
    "sacar_a_la_pausada": (_la_que_paga("paused"), _SACAR_ABRIO, None, {**_SACA, "duena": 409}),
}


@pytest.mark.parametrize("escenario, quien", [
    pytest.param(e, q, id=f"{e}-{q}") for e, (*_, codigos) in _QUIEN_TOCA.items() for q in codigos])
def test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan(client, escenario, quien):
    from tests.test_cobro_mp1 import _leer_org
    preparar, (metodo, ruta), hecho, codigos = _QUIEN_TOCA[escenario]
    nombres, sid, org_id, _ = _org_con_suscripcion(client, quien)
    preparar(nombres, sid, org_id)
    antes = (dict(SUS), {k: _leer(u) for k, u in nombres.items()}, _leer_org(org_id))
    r = getattr(client, metodo)(ruta.format(**nombres), **({"json": {"plan": "premium"}} if "checkout" in ruta else {}))
    codigo = codigos[quien]
    assert r.status_code == codigo, r.text
    if codigo == 200:
        assert hecho(nombres, sid, org_id), r.text
        return
    assert (dict(SUS), {k: _leer(u) for k, u in nombres.items()}, _leer_org(org_id)) == antes
    assert CREADAS == []
    if codigo == 409:
        assert nombres["abrio"] in r.json()["detail"] and "renueva sola" not in r.json()["detail"].lower(), r.text


def _dos_pendientes(client):
    """La org de _org_con_suscripcion con dos pendientes: la de quien abrió y la del
    miembro, que se cancelan en ese orden. La sesión queda en la dueña."""
    nombres, sid, org_id, _ = _org_con_suscripcion(client, "duena")
    otra = f"sus-{nombres['miembro']}"
    SUS[sid] = SUS[otra] = "pending"
    _set_user(nombres["miembro"], mp_preapproval_id=otra)
    assert nombres["abrio"] < nombres["miembro"]
    return nombres, sid, otra, org_id


# PUT: la del miembro se autoriza mientras se cancela la de quien abrió.
# GET: la de quien abrió se autoriza mientras se lee la del miembro, antes de cancelar nada.
@pytest.mark.parametrize("cuando", ["PUT", "GET"])
def test_la_que_se_autoriza_mientras_se_cancelan_las_otras_no_se_cancela(client, cuando):
    nombres, sid, otra, org_id = _dos_pendientes(client)
    dispara, autoriza = (sid, otra) if cuando == "PUT" else (otra, sid)

    def _se_autoriza(request):
        s = _RUTA_SUS.fullmatch(str(request.url)).group(1)
        if request.method == "PUT":
            SUS[s] = "cancelled"
        if request.method == cuando and s == dispara:
            SUS[autoriza] = "authorized"
        return httpx.Response(200, json={"id": s, "status": SUS[s]})
    FALLA["PUT"] = FALLA["GET"] = _se_autoriza
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 409, r.text
    assert SUS[autoriza] == "authorized" and CREADAS == []
    assert SUS[dispara] == ("cancelled" if cuando == "PUT" else "pending")
    assert _leer(nombres["abrio"])["mp_preapproval_id"] == (None if cuando == "PUT" else sid)
    assert _leer(nombres["miembro"])["mp_preapproval_id"] == otra


def test_si_una_no_se_cancela_la_ya_cancelada_en_mp_no_queda_anotada(client):
    nombres, sid, otra, org_id = _dos_pendientes(client)
    SUS[otra] = "cancelled"

    def _falla_la_primera(request):
        s = _RUTA_SUS.fullmatch(str(request.url)).group(1)
        if request.method == "PUT":
            return httpx.Response(500, json={})
        return httpx.Response(200, json={"id": s, "status": SUS[s]})
    FALLA["PUT"] = FALLA["GET"] = _falla_la_primera
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 503, r.text
    assert _leer(nombres["abrio"])["mp_preapproval_id"] == sid
    assert _leer(nombres["miembro"])["mp_preapproval_id"] is None


@pytest.mark.parametrize("lectura, codigo", [("pending", 403), ("cancelled", 403), (_contesta_500, 503)])
def test_un_miembro_cuya_suscripcion_no_paga_no_cancela_el_plan_del_estudio(client, lectura, codigo):
    from tests.test_cobro_mp1 import _leer_org
    nombres, sid, org_id, _ = _org_con_suscripcion(client, "miembro")
    SUS[sid] = "pending"
    assert client.post("/api/billing/checkout", json={"plan": "premium"}).status_code == 200
    assert _leer(nombres["miembro"])["mp_preapproval_id"] == "nueva-1"
    queda = "pending" if callable(lectura) else lectura
    SUS["nueva-1"] = queda
    if callable(lectura):
        FALLA["GET"] = lectura
    r = client.post("/api/billing/cancel")
    assert r.status_code == codigo, r.text
    # Abrió una suscripción: el aviso tiene que decir que no es la que paga.
    assert codigo != 403 or "que lo paga" in r.json()["detail"], r.text
    assert _leer_org(org_id)["billing_status"] == "active" and SUS["nueva-1"] == queda
    assert _leer(nombres["miembro"])["mp_preapproval_id"] == "nueva-1"


class _NoContesta:
    soltar = threading.Event()

    @classmethod
    def esperar(cls, pedido):
        cls.soltar.wait(timeout=10)
        if isinstance(pedido, httpx.Request):
            raise httpx.ReadTimeout("simulado: Mercado Pago no contestó", request=pedido)
        raise TimeoutError("simulado: Mercado Pago no contestó")

    @staticmethod
    def corta_el_sdk(_):
        # El SDK real corta solo a los 10 s, antes del tope, con un error de requests.
        raise requests.exceptions.ConnectTimeout("simulado: Mercado Pago no contestó")


_CANCELAR = ("post", "/api/billing/cancel")
_CHECKOUT = ("post", "/api/billing/checkout")
_REACTIVAR = ("post", "/api/billing/reactivate")
_NO_SE_CONFIRMO_CANCELAR = "No se pudo confirmar la cancelación en Mercado Pago. Probá de nuevo en unos minutos."


# Quién pide, qué, dónde se traba Mercado Pago (al leer, al cancelar o al crear) y
# cómo está la suscripción de quien abrió.
@pytest.mark.parametrize("quien, pedido, traba, estado", [
    ("abrio", _CANCELAR, "GET", "authorized"), ("abrio", _CANCELAR, "PUT", "authorized"),
    ("abrio", _CHECKOUT, "GET", "authorized"), ("abrio", _CHECKOUT, "PUT", "pending"),
    ("abrio", _CHECKOUT, "create", "cancelled"), ("abrio", _CHECKOUT, "create_corta", "cancelled"),
    ("duena", _SACAR_ABRIO, "GET", "pending"), ("duena", _SACAR_ABRIO, "PUT", "pending"),
], ids=["cancelar_lee", "cancelar_cancela", "checkout_lee", "checkout_cancela", "checkout_crea",
        "checkout_crea_sdk_corta", "sacar_lee", "sacar_cancela"])
def test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope(client, monkeypatch, quien, pedido, traba, estado):
    import proyecto_maria.main as main_mod
    from tests.test_cobro_mp1 import _leer_org
    monkeypatch.setattr(main_mod, "_TOPE_MP", 1.0, raising=False)
    nombres, sid, org_id, _ = _org_con_suscripcion(client, quien)
    SUS[sid] = estado
    if traba == "create_corta":
        FALLA["create"] = _NoContesta.corta_el_sdk
    else:
        FALLA[traba] = _NoContesta.esperar
    antes = _leer_org(org_id), {k: _leer(u) for k, u in nombres.items()}
    # La que ya figura cancelada en Mercado Pago deja de figurar aunque después falle.
    antes[1]["abrio"]["mp_preapproval_id"] = None if estado == "cancelled" else sid
    metodo, ruta = pedido
    _NoContesta.soltar.clear()
    try:
        inicio = time.monotonic()
        r = getattr(client, metodo)(ruta.format(**nombres), **({"json": {"plan": "premium"}} if metodo == "post" else {}))
        demora = time.monotonic() - inicio
    finally:
        _NoContesta.soltar.set()
    assert r.status_code == 503, r.text
    assert demora < 3, demora
    assert (_leer_org(org_id), {k: _leer(u) for k, u in nombres.items()}) == antes
    # Mercado Pago pudo haber cancelado igual: el aviso no afirma cómo quedó el plan.
    assert pedido != _CANCELAR or r.json()["detail"] == _NO_SE_CONFIRMO_CANCELAR, r.text


class _Lenta:
    """Cada pedido a Mercado Pago tarda `demora` (entrada simulada, no una espera del caso)."""
    demora = 0.0
    en_curso = 0
    cambio = threading.Condition()

    @classmethod
    def tarda(cls, fn):
        def lenta(*args):
            with cls.cambio:
                cls.en_curso += 1
            try:
                threading.Event().wait(cls.demora)
                return fn(*args)
            finally:
                with cls.cambio:
                    cls.en_curso -= 1
                    cls.cambio.notify_all()
        return lenta


# Cada pedido entra en el tope y la suma lo pasa justo en el pedido n.º `fase`: un
# plazo propio en esa fase la deja terminar (cambia algo, contesta otra cosa o tarda).
@pytest.mark.parametrize("pedido, quien, fase", [
    (_CANCELAR, "duena", 2), (_CANCELAR, "duena", 3), (_REACTIVAR, "duena", 2),
    (_CHECKOUT, "abrio", 2), (_CHECKOUT, "abrio", 3), (_CHECKOUT, "abrio", 4), (_SACAR_ABRIO, "duena", 2),
], ids=["cancelar_lee", "cancelar_cancela", "reactivar_lee", "checkout_relee", "checkout_cancela",
        "checkout_crea", "sacar_cancela"])
def test_el_tope_es_uno_para_todos_los_pedidos_a_mp(client, monkeypatch, pedido, quien, fase):
    import proyecto_maria.main as main_mod
    from tests.test_cobro_mp1 import _leer_org
    tope = 1.0
    monkeypatch.setattr(main_mod, "_TOPE_MP", tope, raising=False)
    if quien == "duena" and pedido != _SACAR_ABRIO:
        nombres, *_, org_id = _dos_pendientes(client)
    else:
        nombres, sid, org_id, _ = _org_con_suscripcion(client, quien)
        SUS[sid] = "pending"
    monkeypatch.setattr(_Lenta, "demora", 0.9 * tope / (fase - 1))
    monkeypatch.setattr(main_mod.httpx, "Client",
                        lambda **kw: httpx.Client(transport=httpx.MockTransport(_Lenta.tarda(_api_mp)), **kw))
    monkeypatch.setattr(_Creador, "create", _Lenta.tarda(_Creador.create))
    antes = _leer_org(org_id), {k: _leer(u) for k, u in nombres.items()}
    if pedido == _CHECKOUT and fase == 4:
        antes[1]["abrio"]["mp_preapproval_id"] = None  # ya cancelada en Mercado Pago
    metodo, ruta = pedido
    inicio = time.monotonic()
    r = getattr(client, metodo)(ruta.format(**nombres), **({"json": {"plan": "premium"}} if pedido == _CHECKOUT else {}))
    demora = time.monotonic() - inicio
    with _Lenta.cambio:
        assert _Lenta.cambio.wait_for(lambda: _Lenta.en_curso == 0, timeout=10)
    assert r.status_code == 503, r.text
    assert demora < 1.4 * tope, demora
    assert (_leer_org(org_id), {k: _leer(u) for k, u in nombres.items()}) == antes
