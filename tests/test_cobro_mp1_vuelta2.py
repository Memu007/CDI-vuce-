"""COBRO-MP-1, vuelta 2 (devolución sobre 784e793, causas b, e y f).

b. Lo que se lee de Mercado Pago sigue una regla: si no se pudo leer, 503
   y una línea de log (Mercado Pago reintenta); si se leyó y no sirve, el
   pago queda «rechazado» con su motivo y 200, a la vista de Emi. Nunca 500.
e. Los mutantes que la PM encontró vivos.
f. Una recarga que no entra en el tope de 100 no se cobra callada.

Mercado Pago simulado: ni el SDK real ni internet.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_cobro_mp1 import (  # noqa: F401
    COBROS, PAGOS, SUSCRIPCIONES, _SDK, _Pagos, _aviso_cobro, _aviso_ipn, _cobros, _fin, _leer_org,
    _leer_pago, _mp, _org, _pago, _pago_de_suscripcion, _renovacion, _sin_suscripciones, _Suscripciones,
    _vencida,
)
from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401


def _en_la_base(funcion):
    """Corre funcion(sesión) contra la base de prueba y devuelve lo que da."""
    from proyecto_maria.database.connection import get_async_session
    salida = []

    async def _run():
        async for db in get_async_session():
            salida.append(await funcion(db))
            await db.commit()
            return
    asyncio.new_event_loop().run_until_complete(_run())
    return salida[0]


def _logs_mp(caplog):
    return [r.getMessage() for r in caplog.records if r.name == "mp_webhook" and r.levelname in ("WARNING", "ERROR")]


# ── b: no se pudo leer el pago → 503 y log ───────────────────────────

def _contesta(estado):
    return lambda self, pid: {"status": estado, "response": {"message": "simulado", "status": estado}}


def _levanta(self, pid):
    raise ConnectionError("simulado: sin conexión")


@pytest.mark.parametrize("get", [
    _contesta(400), _contesta(401), _contesta(403), _contesta(404), _contesta(429), _contesta(500),
    _levanta, lambda self, pid: "no es un objeto", lambda self, pid: {"status": 200, "response": "texto"},
], ids=["http_400", "http_401", "http_403", "http_404", "http_429", "http_500", "excepcion", "no_es_dict",
        "response_no_es_dict"])
def test_si_no_se_puede_leer_el_pago_mercado_pago_reintenta(client, monkeypatch, caplog, get):
    """Con el token vencido Mercado Pago contesta 401 a todo: el aviso
    respondía 200 y el pago se perdía sin rastro."""
    usuario = _unique("v2_lee")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pl-{usuario}", f"{usuario}:premium")
    monkeypatch.setattr(_Pagos, "get", get)
    with caplog.at_level("WARNING", logger="mp_webhook"):
        r = _aviso_ipn(client, pid)
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _logs_mp(caplog), "no quedó una línea de log"


@pytest.mark.parametrize("donde", ["control_de_monto", "renovacion"])
@pytest.mark.parametrize("get", [_contesta(404), _levanta], ids=["http_404", "excepcion"])
def test_si_no_se_puede_leer_la_suscripcion_reintenta(client, monkeypatch, caplog, donde, get):
    usuario = _unique("v2_sus")
    _register(client, usuario)
    _vencida(usuario)
    if donde == "renovacion":
        cobro, pid = _renovacion(usuario)
        avisar = lambda: _aviso_cobro(client, cobro)  # noqa: E731
    else:
        pid = _pago_de_suscripcion(usuario, 30000.0)
        avisar = lambda: _aviso_ipn(client, pid)  # noqa: E731
    monkeypatch.setattr(_Suscripciones, "get", get)
    with caplog.at_level("WARNING", logger="mp_webhook"):
        r = avisar()
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _logs_mp(caplog), "no quedó una línea de log"


@pytest.mark.parametrize("romper", [
    lambda c: c.pop("payment"),
    lambda c: c.update(payment="123"),
    lambda c: c["payment"].pop("id"),
    lambda c: c["payment"].update(id=True),
    lambda c: c["payment"].update(id=""),
    lambda c: c["payment"].update(id=None),
], ids=["sin_pago", "pago_no_es_objeto", "pago_sin_id", "pago_id_booleano", "pago_id_vacio", "pago_id_nulo"])
def test_una_renovacion_que_todavia_no_dice_que_pago_fue_reintenta(client, caplog, romper):
    """Sin el id del pago no hay qué registrar: Mercado Pago reintenta y,
    cuando el cobro ya dice qué pago fue, se aplica."""
    usuario = _unique("v2_cob")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    entero = {**COBROS[cobro], "payment": dict(COBROS[cobro]["payment"])}
    romper(COBROS[cobro])
    with caplog.at_level("WARNING", logger="mp_webhook"):
        r = _aviso_cobro(client, cobro)
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert _logs_mp(caplog), "no quedó una línea de log"
    COBROS[cobro] = entero
    assert _aviso_cobro(client, cobro).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"


@pytest.mark.parametrize("id_en_la_respuesta", [None, True, "", "12/34"], ids=["nulo", "booleano", "vacio", "barra"])
def test_un_pago_aprobado_sin_id_reconocible_reintenta(client, id_en_la_respuesta):
    """Sin un id con qué anotarlo no se puede registrar ni rechazar: 503."""
    usuario = _unique("v2_sinid")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"si-{usuario}", f"{usuario}:premium")
    PAGOS[pid]["id"] = id_en_la_respuesta
    r = _aviso_ipn(client, pid)
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"


# ── b: se leyó y no sirve → rechazado, 200 ───────────────────────────

@pytest.mark.parametrize("referencia", [None, 123, "", "x", "a:b:c:d", "org:x:y:z", "v2:enterprise"],
                         ids=["nula", "numero", "vacia", "sin_dos_puntos", "cuatro_partes", "org_cuatro_partes",
                              "plan_desconocido"])
def test_un_pago_con_referencia_que_no_sirve_queda_rechazado(client, referencia):
    """Antes: 500 con la referencia nula (Mercado Pago reintenta sin fin) y
    400 con una desconocida. El pago está aprobado: Emi lo tiene que ver."""
    pid = _pago(f"pr-{_unique('v2')}", "")
    PAGOS[pid]["external_reference"] = referencia
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200, r.text[:300]
    assert "rechazado" in r.json().get("skipped", ""), r.json()
    fila = _leer_pago(pid)
    assert fila.get("estado") == "rechazado" and fila.get("motivo"), fila


@pytest.mark.parametrize("cuenta", ["usuario", "organizacion"])
def test_un_pago_de_una_cuenta_que_no_existe_queda_rechazado(client, cuenta):
    nombre = _unique("v2_nadie")
    ref = f"{nombre}:premium" if cuenta == "usuario" else "org:00000000-0000-0000-0000-000000000000:premium"
    pid = _pago(f"pn-{nombre}", ref)
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200, r.text[:300]
    fila = _leer_pago(pid)
    assert fila.get("estado") == "rechazado" and "no existe" in (fila.get("motivo") or ""), fila


@pytest.mark.parametrize("referencia", [None, "", 123], ids=["nula", "vacia", "numero"])
def test_una_renovacion_de_una_suscripcion_sin_referencia_queda_rechazada(client, referencia):
    usuario = _unique("v2_sinref")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario)
    SUSCRIPCIONES[f"pre-{usuario}"]["external_reference"] = referencia
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200, r.text[:300]
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid).get("estado") == "rechazado", _leer_pago(pid)


@pytest.mark.parametrize("romper", [
    lambda c: c.pop("preapproval_id"),
    lambda c: c.update(preapproval_id={"id": "x"}),
    lambda c: c.update(preapproval_id=None),
], ids=["sin_suscripcion", "suscripcion_no_es_texto", "suscripcion_nula"])
def test_un_cobro_con_su_pago_y_sin_suscripcion_legible_queda_rechazado(client, romper):
    """El pago trae su referencia y el precio del plan: sólo lo frena que el
    cobro no diga de qué suscripción es."""
    usuario = _unique("v2_cobs")
    _register(client, usuario)
    _vencida(usuario)
    cobro, pid = _renovacion(usuario, monto=45000.0)
    PAGOS[pid]["external_reference"] = f"{usuario}:premium"
    romper(COBROS[cobro])
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200, r.text[:300]
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _leer_pago(pid).get("estado") == "rechazado", _leer_pago(pid)


@pytest.mark.parametrize("campo", ["payer", "card", "card.payment_method"])
def test_un_pago_con_un_dato_secundario_nulo_se_aplica(client, campo):
    """payer y card no deciden nada: en null daban 500."""
    usuario = _unique("v2_nulo")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pz-{usuario}", f"{usuario}:premium")
    if campo == "card.payment_method":
        PAGOS[pid]["card"] = {"last_four_digits": "1234", "payment_method": None}
    else:
        PAGOS[pid][campo] = None
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text[:300]
    assert _get_user(usuario)["billing_status"] == "active"


def test_el_formato_viejo_con_barra_y_sin_payer_se_aplica(client):
    usuario = _unique("v2_barra")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pb-{usuario}", f"{usuario}|premium")
    PAGOS[pid]["payer"] = None
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text[:300]
    assert _get_user(usuario)["billing_status"] == "active"


def test_el_usuario_org_puede_pagar(client):
    """«org:premium» es el plan del usuario «org», no una organización."""
    client.post("/auth/register", json={"username": "org", "password": "SecureP@ss1",
                                        "email": "org@test.billing", "name": "Usuario org"})
    _vencida("org")
    pid = _pago(f"porg-{_unique('v2')}", "org:premium")
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text[:300]
    assert _get_user("org")["billing_status"] == "active"


# ── e: los mutantes vivos ────────────────────────────────────────────

def _inicio_del_registro() -> datetime:
    from proyecto_maria.database.models import InicioRegistroPagosMP

    async def _leer(db):
        return (await db.get(InicioRegistroPagosMP, 1)).desde
    desde = _en_la_base(_leer)
    return desde if desde.tzinfo else desde.replace(tzinfo=timezone.utc)


def test_sin_el_inicio_del_registro_no_se_aplica_nada(client, caplog):
    """Sin la fila no se sabe dónde está el corte: abrirlo volvería a aplicar
    los pagos viejos. 503 hasta que init_db la siembre."""
    from proyecto_maria.database.models import InicioRegistroPagosMP
    usuario = _unique("v2_ini")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pi-{usuario}", f"{usuario}:premium")
    desde = _inicio_del_registro()

    async def _borrar(db):
        await db.delete(await db.get(InicioRegistroPagosMP, 1))

    async def _restaurar(db):
        db.add(InicioRegistroPagosMP(id=1, desde=desde))
    _en_la_base(_borrar)
    try:
        with caplog.at_level("WARNING", logger="mp_webhook"):
            r = _aviso_ipn(client, pid)
    finally:
        _en_la_base(_restaurar)
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert _get_user(usuario)["billing_status"] == "past_due"
    assert _logs_mp(caplog), "no quedó una línea de log"


@pytest.mark.parametrize("corrimiento, aplica", [(-1, False), (1, True)], ids=["un_segundo_antes", "un_segundo_despues"])
def test_el_corte_del_registro_no_tiene_margen(client, corrimiento, aplica):
    usuario = _unique("v2_corte")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pc-{usuario}", f"{usuario}:premium")
    PAGOS[pid]["date_approved"] = (_inicio_del_registro() + timedelta(seconds=corrimiento)).isoformat()
    assert _aviso_ipn(client, pid).status_code == 200
    assert _leer_pago(pid).get("estado") == ("aplicado" if aplica else "rechazado"), _leer_pago(pid)
    assert _get_user(usuario)["billing_status"] == ("active" if aplica else "past_due")


def test_pagar_de_mas_se_aplica(client):
    """El control frena lo que no alcanza; pagar de más no deja sin servicio."""
    usuario = _unique("v2_mas")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pm-{usuario}", f"{usuario}:premium", monto=45000.5)
    assert _aviso_ipn(client, pid).status_code == 200
    assert _leer_pago(pid).get("estado") == "aplicado", _leer_pago(pid)
    assert _get_user(usuario)["billing_status"] == "active"


def test_una_cuenta_en_mora_con_fin_por_delante_suma_desde_hoy(client):
    """past_due no está vigente: aunque su fin quede adelante, el pago suma
    30 días desde hoy y no regala los que quedaban."""
    usuario = _unique("v2_mora")
    _register(client, usuario)
    _set_user(usuario, billing_status="past_due", trial_ends_at=datetime.now(timezone.utc) + timedelta(days=10))
    pid = _pago(f"pmo-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    falta = _fin(_get_user(usuario)) - datetime.now(timezone.utc)
    assert timedelta(days=29) < falta <= timedelta(days=30), falta


def test_el_registro_de_un_pago_de_organizacion_dice_que_es_una_organizacion(client):
    """En el panel, «org:<id>» distingue una organización de un usuario."""
    usuario = _unique("v2_regorg")
    _register(client, usuario)
    org_id = _org(usuario)
    pid = _pago(f"pro-{usuario}", f"org:{org_id}:premium", monto=100.0)
    assert _aviso_ipn(client, pid).status_code == 200
    assert _leer_pago(pid).get("cuenta") == f"org:{org_id}", _leer_pago(pid)


def test_el_panel_muestra_los_ultimos_200_rechazados_del_mas_nuevo_al_mas_viejo(client, monkeypatch):
    from sqlalchemy import delete
    from proyecto_maria.database.models import PagoMercadoPagoAplicado
    prefijo = _unique("v2_panel")
    futuro = datetime.now(timezone.utc) + timedelta(days=3650)
    ids = [f"{prefijo}-{i:03d}" for i in range(201)]

    async def _sembrar(db):
        for i, pid in enumerate(ids):
            db.add(PagoMercadoPagoAplicado(payment_id=pid, cuenta=prefijo, tipo="premium", estado="rechazado",
                                           motivo="sembrado", aplicado_en=futuro + timedelta(seconds=i)))

    async def _retirar(db):
        await db.execute(delete(PagoMercadoPagoAplicado).where(PagoMercadoPagoAplicado.cuenta == prefijo))
    _en_la_base(_sembrar)
    try:
        admin = _unique("v2_admin")
        monkeypatch.setenv("ADMIN_USERNAMES", admin)
        _register(client, admin)
        r = client.get("/api/dev/pagos-mp-rechazados")
    finally:
        _en_la_base(_retirar)
    assert r.status_code == 200, r.text[:300]
    vistos = [p["payment_id"] for p in r.json()["pagos"]]
    assert vistos == list(reversed(ids))[:200], vistos[:3]


def test_el_panel_nombra_todos_los_motivos_de_rechazo():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "proyecto_maria/templates/dev_dashboard.html").read_text()
    for motivo in ("precio", "moneda", "fecha", "tope"):
        assert motivo in html.split("Pagos de Mercado Pago no aplicados", 1)[1][:1500], motivo


# ── f: la recarga y el tope de 100 ───────────────────────────────────

class _Preferencias:
    creadas: list = []

    def create(self, datos):
        _Preferencias.creadas.append(datos)
        return {"status": 201, "response": {"id": "pref-1", "init_point": "https://mp.test/pagar",
                                            "sandbox_init_point": "https://sandbox.mp.test/pagar"}}


class _SDKConPreferencias(_SDK):
    def preference(self):
        return _Preferencias()


@pytest.fixture
def preferencias(monkeypatch):
    import proyecto_maria.main as main_mod
    monkeypatch.setenv("MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setattr(main_mod.mercadopago, "SDK", _SDKConPreferencias)
    _Preferencias.creadas = []
    return _Preferencias.creadas


def _con_extras(usuario: str, cuenta: str, extras: int, vencen: datetime):
    if cuenta == "usuario":
        _set_user(usuario, extra_ops_remaining=extras, extra_ops_expires_at=vencen)
        return None
    org_id = _org(usuario, extra_ops_remaining=extras, extra_ops_expires_at=vencen)
    _set_user(usuario, organization_id=org_id)
    return org_id


@pytest.mark.parametrize("cuenta", ["usuario", "organizacion"])
@pytest.mark.parametrize("extras", [95, 100])
def test_con_el_tope_lleno_no_se_arma_el_link_de_recarga(client, preferencias, cuenta, extras):
    usuario = _unique("v2_tope")
    _register(client, usuario)
    _con_extras(usuario, cuenta, extras, datetime.now(timezone.utc) + timedelta(days=10))
    r = client.post("/api/billing/topup", json={})
    assert r.status_code == 409, r.text[:300]
    detalle = r.json().get("detail", "")
    assert str(extras) in detalle and "100" in detalle, detalle
    assert preferencias == [], "se armó el link de una recarga que no entra"


@pytest.mark.parametrize("cuenta", ["usuario", "organizacion"])
def test_con_los_extras_vencidos_se_puede_recargar(client, preferencias, cuenta):
    usuario = _unique("v2_venc")
    _register(client, usuario)
    org_id = _con_extras(usuario, cuenta, 100, datetime.now(timezone.utc) - timedelta(days=1))
    r = client.post("/api/billing/topup", json={})
    assert r.status_code == 200 and r.json().get("init_point"), r.text[:300]
    esperada = f"org:{org_id}:topup" if org_id else f"{usuario}:topup"
    assert preferencias[0]["external_reference"] == esperada, preferencias


@pytest.mark.parametrize("cuenta", ["usuario", "organizacion"])
@pytest.mark.parametrize("extras", [95, 100])
def test_una_recarga_que_no_entra_queda_rechazada_y_no_suma(client, cuenta, extras):
    """Antes se cobraba y quedaba «aplicado» acreditando 5 o nada."""
    usuario = _unique("v2_recno")
    _register(client, usuario)
    org_id = _con_extras(usuario, cuenta, extras, datetime.now(timezone.utc) + timedelta(days=10))
    ref = f"org:{org_id}:topup" if org_id else f"{usuario}:topup"
    pid = _pago(f"pt-{usuario}", ref, monto=10000.0)
    assert _aviso_ipn(client, pid).status_code == 200
    despues = _leer_org(org_id) if org_id else _get_user(usuario)
    assert despues["extra_ops_remaining"] == extras, despues
    fila = _leer_pago(pid)
    assert fila.get("estado") == "rechazado" and "tope" in (fila.get("motivo") or ""), fila


@pytest.mark.parametrize("extras, vencen, queda", [
    (90, timedelta(days=10), 100), (100, timedelta(days=-1), 10),
], ids=["llega_justo_a_100", "los_vencidos_no_cuentan"])
def test_una_recarga_que_entra_suma_entera(client, extras, vencen, queda):
    usuario = _unique("v2_recsi")
    _register(client, usuario)
    _con_extras(usuario, "usuario", extras, datetime.now(timezone.utc) + vencen)
    pid = _pago(f"pt-{usuario}", f"{usuario}:topup", monto=10000.0)
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["extra_ops_remaining"] == queda, _get_user(usuario)
    assert _leer_pago(pid).get("estado") == "aplicado", _leer_pago(pid)
