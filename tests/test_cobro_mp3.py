"""Cobro con Mercado Pago: lo que hace un Mercado Pago lento o un aviso ajeno.

- Una consulta a Mercado Pago que tarda no frena al resto del servidor.
- El aviso de pago tiene un límite de pedidos.
- Un aviso sin firma verificable no cambia nada ni consulta a Mercado Pago.

Mercado Pago simulado: ni el SDK real ni internet.
"""
import asyncio
import threading
from datetime import datetime, timezone

import httpx
import pytest

from tests.mp_firma import aviso_firmado
from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401

SECRETO = "secreto-de-prueba"
PAGOS: dict = {}
LLAMADAS: list = []   # (método del SDK, si corrió en el hilo del loop)


class _Trabado:
    """Mercado Pago que no contesta hasta que la prueba lo suelta."""
    soltar = threading.Event()
    lock = threading.Lock()
    adentro = 0
    maximo = 0

    @classmethod
    def esperar(cls, metodo: str):
        try:
            asyncio.get_running_loop()
            LLAMADAS.append((metodo, True))
            return
        except RuntimeError:
            LLAMADAS.append((metodo, False))
        with cls.lock:
            cls.adentro += 1
            cls.maximo = max(cls.maximo, cls.adentro)
        try:
            cls.soltar.wait(timeout=60)
        finally:
            with cls.lock:
                cls.adentro -= 1


class _Pagos:
    def get(self, pid):
        _Trabado.esperar("payment.get")
        return {"status": 200, "response": PAGOS[str(pid)]}


class _Creador:
    def __init__(self, tipo):
        self.tipo = tipo

    def create(self, datos):
        _Trabado.esperar(f"{self.tipo}.create")
        return {"status": 201, "response": {"id": f"{self.tipo}-1", "init_point": "https://mp.example/x"}}


class _SDK:
    def __init__(self, token, **kw):
        pass

    def payment(self):
        return _Pagos()

    def preapproval(self):
        return _Creador("preapproval")

    def preference(self):
        return _Creador("preference")


@pytest.fixture(autouse=True)
def _mp(monkeypatch):
    import proyecto_maria.main as main_mod
    monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", SECRETO)
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
    monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setenv("MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setenv("MP_PREAPPROVAL_PLAN_ID_PREMIUM", "plan-premium")
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setattr(main_mod.mercadopago, "SDK", _SDK)
    PAGOS.clear()
    LLAMADAS.clear()
    _Trabado.soltar.clear()
    _Trabado.adentro = _Trabado.maximo = 0
    yield
    _Trabado.soltar.set()


async def _hasta(condicion, segundos: float = 15):
    limite = asyncio.get_running_loop().time() + segundos
    while not condicion():
        assert asyncio.get_running_loop().time() < limite, "no se cumplió a tiempo"
        await asyncio.sleep(0.01)


def _tope() -> int:
    import proyecto_maria.main as main_mod
    limitador = getattr(main_mod, "_HILOS_MP", None)
    return int(limitador.total_tokens) if limitador else 40


def test_un_mercado_pago_trabado_no_frena_el_servidor(client):
    """Con más consultas trabadas en Mercado Pago que hilos tiene el servidor,
    entrar a la cuenta sigue contestando; las consultas no pasan su tope."""
    import proyecto_maria.main as main_mod
    usuario = _unique("mp3_tr")
    _register(client, usuario)
    cookies = dict(client.cookies)
    client.cookies.clear()
    trabadas = 45
    for i in range(trabadas):
        PAGOS[f"t{i}"] = {"id": f"t{i}", "status": "rejected"}

    async def _correr():
        transporte = httpx.ASGITransport(app=main_mod.app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test") as anon, \
                httpx.AsyncClient(transport=transporte, base_url="http://test", cookies=cookies) as suyo:
            pedidos = [asyncio.create_task(anon.post("/api/payments/webhook", **aviso_firmado("payment", f"t{i}", SECRETO)))
                       for i in range(trabadas - 2)]
            pedidos.append(asyncio.create_task(suyo.post("/api/billing/checkout", json={"plan": "premium"})))
            pedidos.append(asyncio.create_task(suyo.post("/api/billing/topup", json={})))
            try:
                await _hasta(lambda: any(en_loop for _, en_loop in LLAMADAS) or _Trabado.adentro >= _tope())
                entra = await asyncio.wait_for(
                    anon.post("/auth/login", json={"username": usuario, "password": "SecureP@ss1"}), 15)
            finally:
                _Trabado.soltar.set()
            return entra, await asyncio.gather(*pedidos)

    entra, respuestas = asyncio.new_event_loop().run_until_complete(_correr())
    assert [m for m, en_loop in LLAMADAS if en_loop] == []
    assert entra.status_code == 200, entra.text
    assert _Trabado.maximo <= _tope() < 40
    assert {r.status_code for r in respuestas} == {200}, [r.text[:120] for r in respuestas if r.status_code != 200]
    assert {m for m, _ in LLAMADAS} == {"payment.get", "preapproval.create", "preference.create"}


def test_el_aviso_de_pago_tiene_limite_de_pedidos(client):
    """Los avisos sin firma de una IP no le gastan el cupo a los firmados."""
    from proyecto_maria.core.rate_limit import limiter
    ip = {"x-forwarded-for": "198.51.100.7"}

    def _firmado(i):
        aviso = aviso_firmado("otro", f"x{i}", SECRETO)
        return client.post("/api/payments/webhook", content=aviso["content"], headers={**aviso["headers"], **ip})
    limiter.reset()
    limiter.enabled = True
    try:
        sin_firma = {client.post("/api/payments/webhook", content="x", headers=ip).status_code for _ in range(60)}
        codigos = [_firmado(i).status_code for i in range(61)]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert sin_firma == {401}
    assert codigos[:60] == [200] * 60 and codigos[60] == 429, codigos


_SIN_FIRMA = {
    "ipn": {"url": "/api/payments/webhook?topic=payment&id={pid}"},
    "ipn de cobro": {"url": "/api/payments/webhook?topic=subscription_authorized_payment&id={pid}"},
    "json sin firma": {"url": "/api/payments/webhook",
                       "content": '{{"type": "payment", "data": {{"id": "{pid}"}}}}'},
    "firma con otra clave": {"url": "/api/payments/webhook", "clave": "otra-clave"},
    "firmado con clave vacía": {"url": "/api/payments/webhook", "clave": ""},
    "sólo los primeros caracteres": {"url": "/api/payments/webhook", "clave": SECRETO,
                                     "v1": lambda v: v[:8] + "".join("1" if c == "0" else "0" for c in v[8:])},
    **{f"el carácter {i} cambiado": {"url": "/api/payments/webhook", "clave": SECRETO,
                                     "v1": lambda v, i=i: v[:i] + ("1" if v[i] == "0" else "0") + v[i + 1:]}
       for i in range(64)},
    "dos v1, la buena primero": {"url": "/api/payments/webhook", "clave": SECRETO, "v1": lambda v: f"{v},v1={v[::-1]}"},
    "dos v1, la buena al final": {"url": "/api/payments/webhook", "clave": SECRETO, "v1": lambda v: f"{v[::-1]},v1={v}"},
    "firma más corta": {"url": "/api/payments/webhook", "clave": SECRETO, "v1": lambda v: v[:-1]},
    "firma más larga": {"url": "/api/payments/webhook", "clave": SECRETO, "v1": lambda v: v + "0"},
    "cuerpo que no es un objeto": {"url": "/api/payments/webhook", "content": '["{pid}"]', "firma": b"ts=1,v1=00"},
    "data que no es un objeto": {"url": "/api/payments/webhook", "content": '{{"data": ["{pid}"]}}',
                                 "firma": b"ts=1,v1=00"},
    "firma con letras no ascii": {"url": "/api/payments/webhook", "content": '{{"data": {{"id": "{pid}"}}}}',
                                  "firma": "ts=1,v1=é".encode()},
}


@pytest.mark.parametrize("produccion", [False, True], ids=["dev", "produccion"])
@pytest.mark.parametrize("secreto", [SECRETO, ""], ids=["con-secreto", "sin-secreto"])
def test_un_aviso_sin_firma_verificable_no_cambia_nada(client, monkeypatch, secreto, produccion):
    import proyecto_maria.main as main_mod
    monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", secreto)
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", produccion)
    _Trabado.soltar.set()
    usuario = _unique("mp3_sf")
    _register(client, usuario)
    client.cookies.clear()
    _set_user(usuario, billing_status="past_due", ops_used_this_period=7)
    antes = _get_user(usuario)
    for i, (nombre, aviso) in enumerate(_SIN_FIRMA.items()):
        pid = f"sf-{i}-{usuario}"
        PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": f"{usuario}:premium",
                      "transaction_amount": 45000.0, "currency_id": "ARS", "payer": {"id": "p"},
                      "date_approved": datetime.now(timezone.utc).isoformat()}
        if "clave" in aviso:
            firmado = aviso_firmado("payment", pid, aviso["clave"])
            if "v1" in aviso:
                ts, real = firmado["headers"]["x-signature"].split(",v1=")
                firmado["headers"]["x-signature"] = f"{ts},v1={aviso['v1'](real)}"
            r = client.post(aviso["url"], **firmado)
        else:
            firma = {"x-signature": aviso["firma"], "x-request-id": "r"} if aviso.get("firma") else {}
            r = client.post(aviso["url"].format(pid=pid), content=aviso.get("content", "").format(pid=pid),
                            headers=firma)
        assert r.status_code == 401, (nombre, r.status_code, r.text[:200])
    assert LLAMADAS == []
    assert _get_user(usuario) == antes


def test_la_recarga_con_mercado_pago_cortado_da_503(client, monkeypatch):
    """El SDK corta solo con un error de requests: es que Mercado Pago no contestó."""
    import requests

    def _corta(self, datos):
        raise requests.exceptions.ConnectTimeout("simulado: Mercado Pago no contestó")
    monkeypatch.setattr(_Creador, "create", _corta)
    _register(client, _unique("mp3_rc"))
    r = client.post("/api/billing/topup", json={})
    assert r.status_code == 503, r.text
