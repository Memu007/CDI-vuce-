"""ABUSO-1 (S4, S5, S6 y C9 de AUDITORIA-2026-10-06).

S5: las rutas de eventos (`/api/ui/event` y `/api/session/state`, sin sesión
obligatoria) guardaban cualquier cuerpo: cada pedido de 5 MB sumaba 5 MB a
`logs/ui_events.jsonl`, que ningún código lee, y una fila de 8000 caracteres
en `telemetry_events`. Ahora el cuerpo tiene un tope de 16 KB (lo que se pasa
da 413 y no se guarda) y el JSONL ya no se escribe.

S4: los límites tomaban la primera IP de X-Forwarded-For, que la escribe el
cliente; ahora toman la última, la que agrega el proxy. S6 y C9: recuperar
usuario y el registro no tenían límite. Los contadores de login, reset,
registro y recuperar viven en la tabla `limites_auth`. Los eventos tienen 120
por minuto por ruta y, sin sesión, se guardan sólo los de una lista.

Acá corre en SQLite; el mismo recorrido contra un servidor real, en Postgres y
en SQLite, está en `scripts/testing/abuso1_motores.py`.
"""
import asyncio
import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import proyecto_maria.database.connection as conn
import proyecto_maria.main as main_mod
from proyecto_maria.main import app

RUTAS = ("/api/ui/event", "/api/session/state")
TOPE = 16 * 1024
JSONL = os.path.join(main_mod.basedir, "logs", "ui_events.jsonl")
CLAVE = "Clave-sintetica-1!"


@pytest.fixture(scope="module", autouse=True)
def _tablas():
    with TestClient(app):
        pass
    yield


@pytest.fixture(autouse=True)
def _limites_limpios(monkeypatch):
    """Cada caso arranca con los contadores en cero y el limitador como lo
    dejó la app (otro módulo puede haberlo apagado)."""
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    from proyecto_maria.core.rate_limit import limiter
    antes = limiter.enabled
    limiter.enabled = True
    limiter.reset()
    asyncio.run(_vaciar_limites())
    yield
    limiter.reset()
    limiter.enabled = antes


async def _vaciar_limites():
    async with conn.AsyncSessionLocal() as s:
        await s.execute(text("delete from limites_auth"))
        await s.commit()


def _filas(accion):
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(text(
                "select owner_username, length(props) from telemetry_events where action = :a"), {"a": accion})
            return [tuple(x) for x in r.all()]
    return asyncio.run(_correr())


def _tamano_jsonl():
    return os.path.getsize(JSONL) if os.path.exists(JSONL) else 0


def _cuerpo(accion, total):
    """Un evento JSON válido de exactamente `total` bytes."""
    base = '{"action":"%s","screen":"s","relleno":"' % accion
    return (base + "x" * (total - len(base) - 2) + '"}').encode()


@pytest.fixture(scope="module")
def token():
    u = "ab1t_" + uuid.uuid4().hex[:8]
    with TestClient(app) as c:
        r = c.post("/auth/register", headers={"X-Forwarded-For": _ip()},
                   json={"username": u, "password": CLAVE,
                         "email": f"{u}@ejemplo.test", "name": "Ab"})
        assert r.status_code == 200, r.text
        return u, r.json()["access_token"]


def _accion():
    return "ab1_" + uuid.uuid4().hex[:10]


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("con_sesion", (False, True))
def test_s5_evento_de_5mb_no_se_guarda(ruta, con_sesion, token):
    a = _accion()
    h = {"Content-Type": "application/json"}
    if con_sesion:
        h["Authorization"] = f"Bearer {token[1]}"
    antes = _tamano_jsonl()
    r = TestClient(app).post(ruta, content=_cuerpo(a, 5 * 1024 * 1024), headers=h)
    assert r.status_code == 413, (r.status_code, r.text[:200])
    assert _filas(a) == []
    assert _tamano_jsonl() == antes


@pytest.mark.parametrize("ruta", RUTAS)
def test_s5_sin_content_length_tambien_corta(ruta):
    """Un cuerpo por partes (sin Content-Length) se corta al pasar el tope."""
    a = _accion()
    cuerpo = _cuerpo(a, 1024 * 1024)

    def partes():
        for i in range(0, len(cuerpo), 4096):
            yield cuerpo[i:i + 4096]

    r = TestClient(app).post(ruta, content=partes(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413, (r.status_code, r.text[:200])
    assert _filas(a) == []


@pytest.mark.parametrize("ruta", RUTAS)
def test_s5_el_tope_es_16kb(ruta, token):
    h = {"Content-Type": "application/json", "Authorization": f"Bearer {token[1]}"}
    justo, pasado = _accion(), _accion()
    r = TestClient(app).post(ruta, content=_cuerpo(justo, TOPE), headers=h)
    assert r.status_code == 200 and r.json()["ok"] is True, r.text
    assert [u for u, _ in _filas(justo)] == [token[0]]
    r = TestClient(app).post(ruta, content=_cuerpo(pasado, TOPE + 1), headers=h)
    assert r.status_code == 413, r.text
    assert _filas(pasado) == []


@pytest.mark.parametrize("ruta", RUTAS)
def test_s5_un_evento_chico_se_guarda_y_no_escribe_el_jsonl(ruta, token):
    a = _accion()
    antes = _tamano_jsonl()
    r = TestClient(app).post(ruta, json={"action": a, "screen": "s", "version": "v2"},
                             headers={"Authorization": f"Bearer {token[1]}"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text
    assert [u for u, _ in _filas(a)] == [token[0]]
    assert _tamano_jsonl() == antes


# --- S4, S6, C9 y eventos (D35) -------------------------------------------
# Cada caso usa IPs sintéticas propias (rango de documentación 2001:db8::/32)
# que llegan como la última entrada de X-Forwarded-For, como las agrega el
# proxy de Railway; así los contadores de un caso no tocan los de otro.


def _ip():
    h = uuid.uuid4().hex
    return f"2001:db8::{h[:4]}:{h[4:8]}"


def _xff(real, inventada=None):
    return {"X-Forwarded-For": f"{inventada}, {real}" if inventada else real}


def _req(xffs, host="10.0.0.1"):
    from starlette.requests import Request
    return Request({"type": "http", "method": "GET", "path": "/", "client": (host, 1234),
                    "headers": [(b"x-forwarded-for", v.encode()) for v in xffs]})


@pytest.mark.parametrize("xffs,saltos,esperada", [
    (["203.0.113.1, 198.51.100.2"], None, "198.51.100.2"),
    (["203.0.113.1, 198.51.100.2"], "2", "203.0.113.1"),
    (["203.0.113.1, 198.51.100.2"], "0", "10.0.0.1"),
    (["198.51.100.2"], "2", "198.51.100.2"),
    (["203.0.113.1", "198.51.100.2"], None, "198.51.100.2"),
    ([" , 198.51.100.3, "], None, "198.51.100.3"),
    ([" ,  "], None, "10.0.0.1"),
    ([], None, "10.0.0.1"),
    (["203.0.113.1, 198.51.100.2"], "abc", "198.51.100.2"),
    (["203.0.113.1, 198.51.100.2"], "-1", "198.51.100.2"),
])
def test_s4_la_ip_es_la_ultima_de_x_forwarded_for(xffs, saltos, esperada, monkeypatch):
    from proyecto_maria.core.rate_limit import get_client_ip
    if saltos is None:
        monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    else:
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", saltos)
    assert get_client_ip(_req(xffs)) == esperada


def _login(c, usuario, clave, real, inventada=None):
    return c.post("/auth/login", json={"username": usuario, "password": clave},
                  headers=_xff(real, inventada))


def test_s4a_una_ip_inventada_no_esquiva_el_bloqueo_del_login():
    """Con el limitador por minuto apagado queda sólo el bloqueo por fallos:
    cinco fallos desde la misma IP real bloquean aunque cada pedido invente
    otra IP al principio de X-Forwarded-For."""
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    real, c = _ip(), TestClient(app)
    codigos = [_login(c, "nadie_" + uuid.uuid4().hex[:6], "x", real, _ip()).status_code for _ in range(5)]
    assert codigos == [401] * 5
    r = _login(c, "nadie", "x", real, _ip())
    assert r.status_code == 429 and "Demasiados intentos fallidos" in r.text, (r.status_code, r.text)


def test_s4b_una_ip_inventada_no_bloquea_a_otro(token):
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    victima, atacante, c = _ip(), _ip(), TestClient(app)
    for _ in range(6):
        _login(c, "nadie", "x", atacante, victima)
    r = _login(c, token[0], CLAVE, victima)
    assert r.status_code == 200, (r.status_code, r.text)


def test_s4_el_limite_por_minuto_del_login_cuenta_la_ip_real(token):
    """El 5/minuto de slowapi en el login: seis logins correctos desde la misma
    IP real, inventando otra cada vez; el sexto da 429."""
    real, c = _ip(), TestClient(app)
    codigos = [_login(c, token[0], CLAVE, real, _ip()).status_code for _ in range(6)]
    assert codigos == [200] * 5 + [429], codigos


@pytest.mark.parametrize("larga", (False, True))
def test_s4_el_login_correcto_borra_los_fallos(token, larga):
    """Cuatro fallos, un login correcto, cuatro fallos más: no bloquea, porque
    el correcto vuelve la cuenta a cero (también con una IP más larga que la
    clave de la tabla)."""
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    real, c = (_ip_larga() if larga else _ip()), TestClient(app)
    for _ in range(2):
        codigos = [_login(c, token[0], "mal", real).status_code for _ in range(4)]
        assert codigos == [401] * 4, codigos
        r = _login(c, token[0], CLAVE, real)
        assert r.status_code == 200, (r.status_code, r.text)


def test_s4_el_429_del_login_deja_ip_y_entradas_en_el_log(caplog):
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    real, c = _ip(), TestClient(app)
    for _ in range(5):
        _login(c, "nadie", "x", real, _ip())
    with caplog.at_level("WARNING", logger="proyecto_maria.core.rate_limit"):
        r = _login(c, "nadie", "x", real, "203.0.113.9")
    assert r.status_code == 429, r.text
    lineas = [x.getMessage() for x in caplog.records if x.name == "proyecto_maria.core.rate_limit"]
    assert any(f"ip={real}" in m and "entradas_xff=2" in m and "/auth/login" in m for m in lineas), lineas


RECUPERAR = "/auth/recover-username"
MSJ_RECUPERAR = "Si el email está registrado, te enviamos tu nombre de usuario."


@pytest.fixture
def reloj(monkeypatch):
    """Reloj de los contadores, fijo y movible. Se pide después de la primera
    aserción de comportamiento para que, sin el arreglo, el caso falle por lo
    que mide y no por el import."""
    def mover(segundos=0.0):
        from proyecto_maria.core import limites_auth
        if not hasattr(mover, "t"):
            mover.t = limites_auth._ahora()
        mover.t += segundos
        monkeypatch.setattr(limites_auth, "_ahora", lambda: mover.t)
    return mover


@pytest.mark.parametrize("ruta,cuerpo,pasa", [
    ("/auth/login", {"username": "nadie", "password": "x"}, 401),
    ("/auth/request-password-reset", {"email": "n@ejemplo.test"}, 200),
    (RECUPERAR, {"email": "n@ejemplo.test"}, 200),
])
def test_los_limites_por_ip_duran_quince_minutos(ruta, cuerpo, pasa, reloj):
    """Cinco pedidos y el sexto da 429; a los 14 minutos sigue cortado y a los
    16 vuelve a pasar. El login, sin el 5/minuto de slowapi."""
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = ruta != "/auth/login"
    real, c = _ip(), TestClient(app)
    codigos = [c.post(ruta, json=cuerpo, headers=_xff(real, _ip())).status_code for _ in range(6)]
    assert codigos == [pasa] * 5 + [429], codigos
    reloj()
    reloj(14 * 60)
    assert c.post(ruta, json=cuerpo, headers=_xff(real)).status_code == 429
    reloj(2 * 60)
    r = c.post(ruta, json=cuerpo, headers=_xff(real))
    assert r.status_code == pasa, (r.status_code, r.text)


def test_s6_recuperar_usuario_corta_en_silencio_por_email(token, monkeypatch, reloj):
    """Tres pedidos por hora para un mismo email, cuente como venga escrito;
    el cuarto contesta lo mismo pero no manda el mail. Desde EMAIL-1 cada
    variante encuentra la cuenta y el mail va a la dirección guardada. La
    ventana es de una hora."""
    enviados = []
    monkeypatch.setattr(main_mod, "send_email", lambda to, *a, **k: enviados.append(to) or True)
    email = f"{token[0]}@ejemplo.test"
    c = TestClient(app)
    for variante in (email.upper(), email.capitalize(), email):
        r = c.post(RECUPERAR, json={"email": variante}, headers=_xff(_ip()))
        assert r.status_code == 200 and r.json() == {"message": MSJ_RECUPERAR}, r.text
    assert enviados == [email] * 3
    r = c.post(RECUPERAR, json={"email": email}, headers=_xff(_ip()))
    assert r.status_code == 200 and r.json() == {"message": MSJ_RECUPERAR}, r.text
    assert enviados == [email] * 3, "el cuarto pedido de la hora mandó el mail"
    reloj()
    reloj(59 * 60)
    c.post(RECUPERAR, json={"email": email}, headers=_xff(_ip()))
    assert enviados == [email] * 3, "a los 59 minutos ya mandó otro"
    reloj(2 * 60)
    c.post(RECUPERAR, json={"email": email}, headers=_xff(_ip()))
    assert enviados == [email] * 4, "pasada la hora no volvió a mandar"


def _registrar(c, real):
    u = "ab1r_" + uuid.uuid4().hex[:8]
    return c.post("/auth/register", headers=_xff(real, _ip()),
                  json={"username": u, "password": CLAVE, "email": f"{u}@ejemplo.test", "name": "Ab"})


def test_c9_registro_cinco_por_hora(reloj):
    real, c = _ip(), TestClient(app)
    codigos = [_registrar(c, real).status_code for _ in range(6)]
    assert codigos == [200] * 5 + [429], codigos
    reloj()
    reloj(3600 + 1)
    r = _registrar(c, real)
    assert r.status_code == 200, r.text


def test_c9_registro_veinte_por_dia(reloj):
    real, c = _ip(), TestClient(app)
    for hora in range(4):
        codigos = [_registrar(c, real).status_code for _ in range(5)]
        assert codigos == [200] * 5, (hora, codigos)
        if hora == 0:
            reloj()
        reloj(3600 + 1)
    r = _registrar(c, real)
    assert r.status_code == 429, (r.status_code, r.text)
    reloj(24 * 3600)
    assert _registrar(c, real).status_code == 200


def _filas_marca(marca):
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(text(
                "select owner_username, action from telemetry_events where props like :m"), {"m": f"%{marca}%"})
            return [tuple(x) for x in r.all()]
    return asyncio.run(_correr())


@pytest.mark.parametrize("ruta,otra", [RUTAS, RUTAS[::-1]])
def test_eventos_120_por_minuto_por_ruta(ruta, otra, token):
    real, c = _ip(), TestClient(app)
    h = {"Authorization": f"Bearer {token[1]}"}
    codigos = [c.post(ruta, json={"action": "ab1_lote"}, headers={**h, **_xff(real, _ip())}).status_code
               for _ in range(121)]
    assert codigos.count(200) == 120 and codigos[-1] == 429, (codigos.count(200), codigos[-3:])
    r = c.post(otra, json={"action": "ab1_lote"}, headers={**h, **_xff(real)})
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("accion", ("pricing_cta_clicked", "hero_cta_clicked", "register_pending_verify"))
def test_eventos_sin_sesion_permitidos_se_guardan(ruta, accion):
    marca = uuid.uuid4().hex
    r = TestClient(app).post(ruta, json={"action": accion, "marca": marca}, headers=_xff(_ip()))
    assert r.status_code == 200 and r.json()["ok"] is True, r.text
    assert _filas_marca(marca) == [(None, accion)]


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("accion", ("click", "pricing_cta_clicked_x", "Hero_CTA_clicked", ""))
def test_eventos_sin_sesion_no_permitidos_no_se_guardan(ruta, accion, token):
    marca = uuid.uuid4().hex
    c = TestClient(app)
    r = c.post(ruta, json={"action": accion, "marca": marca}, headers=_xff(_ip()))
    assert r.status_code == 200 and r.json()["ok"] is False, r.text
    assert _filas_marca(marca) == []
    # La misma acción con sesión sí se guarda: lo que corta es la falta de sesión.
    # Otros casos entran con el mismo usuario y eso revoca el token del registro.
    vigente = _login(c, token[0], CLAVE, _ip()).json()["access_token"]
    r = c.post(ruta, json={"action": accion or "x", "marca": marca}, headers={
        "Authorization": f"Bearer {vigente}", **_xff(_ip())})
    assert r.json()["ok"] is True and [u for u, _ in _filas_marca(marca)] == [token[0]], r.text


def _filas_limites(*claves):
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(text("select clave from limites_auth"))
            return sorted(c for (c,) in r.all() if c in claves)
    return asyncio.run(_correr())


def _sembrar_limites(**vence_en):
    """Inserta filas con `vence` a tantos segundos de ahora (negativo: vencida)."""
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            for clave, seg in vence_en.items():
                await s.execute(text(
                    "insert into limites_auth (clave, cuenta, bloqueado_hasta, vence) values (:c, 9, 0, :v)"),
                    {"c": clave, "v": time.time() + seg})
            await s.commit()
    asyncio.run(_correr())


@pytest.mark.parametrize("ruta", ("/auth/recover-username", "/auth/request-password-reset"))
def test_tabla_las_vencidas_se_borran_al_escribir(ruta):
    """Recuperar usuario cuenta pedidos y recuperar contraseña suma fallos:
    las dos escrituras borran antes las vencidas."""
    _sembrar_limites(ab1_vieja=-1, ab1_viva=600)
    r = TestClient(app).post(ruta, json={"email": "n@ejemplo.test"}, headers=_xff(_ip()))
    assert r.status_code == 200, r.text
    assert _filas_limites("ab1_vieja", "ab1_viva") == ["ab1_viva"]


def test_tabla_las_vencidas_se_borran_al_arrancar():
    _sembrar_limites(ab1_vieja=-1, ab1_viva=600)
    with TestClient(app):
        pass
    assert _filas_limites("ab1_vieja", "ab1_viva") == ["ab1_viva"]


RESET = "/auth/request-password-reset"


def test_reset_cinco_y_despues_uno_cada_quince_minutos(reloj):
    """Lo que ya hacía en memoria: cinco pedidos, bloqueo de 15 minutos, y
    vencido el bloqueo pasa uno solo antes de volver a bloquear."""
    real, c = _ip(), TestClient(app)
    codigos = [c.post(RESET, json={"email": f"n{i}@ejemplo.test"}, headers=_xff(real, _ip())).status_code
               for i in range(6)]
    assert codigos == [200] * 5 + [429], codigos
    reloj()
    reloj(15 * 60 + 1)
    codigos = [c.post(RESET, json={"email": f"m{i}@ejemplo.test"}, headers=_xff(real)).status_code
               for i in range(2)]
    assert codigos == [200, 429], codigos


def test_reset_pedidos_simultaneos_no_pasan_el_tope():
    """Veinte pedidos a la vez desde una IP: pasan cinco, como en fila."""
    import httpx
    real = _ip()

    async def _correr():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            rs = await asyncio.gather(*(c.post(RESET, json={"email": f"s{i}@ejemplo.test"}, headers=_xff(real))
                                        for i in range(20)))
            return sorted(r.status_code for r in rs)
    codigos = asyncio.run(_correr())
    assert codigos == [200] * 5 + [429] * 15, codigos


def test_c9_registros_simultaneos_no_pasan_el_tope():
    """Veinte registros a la vez desde una IP: pasan cinco, como en fila."""
    import httpx
    real = _ip()

    async def _correr():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            rs = await asyncio.gather(*(c.post("/auth/register", headers=_xff(real), json={
                "username": f"ab1s_{uuid.uuid4().hex[:8]}", "password": CLAVE,
                "email": f"ab1s_{uuid.uuid4().hex[:8]}@ejemplo.test", "name": "Ab"}) for _ in range(20)))
            return sorted(r.status_code for r in rs)
    codigos = asyncio.run(_correr())
    assert codigos == [200] * 5 + [429] * 15, codigos


def _ip_larga():
    # Sin proxy delante (o si Railway no agrega su entrada), la última de
    # X-Forwarded-For la escribe el cliente y puede tener cualquier largo.
    return "x" * 300 + uuid.uuid4().hex


def _claves_largas():
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(text("select clave from limites_auth"))
            return [c for (c,) in r.all() if len(c) > 120]
    return asyncio.run(_correr())


def _cuerpo_auth(ruta):
    u = "ab1l_" + uuid.uuid4().hex[:8]
    return {"/auth/login": {"username": "nadie", "password": "x"},
            "/auth/register": {"username": u, "password": CLAVE, "email": f"{u}@ejemplo.test", "name": "Ab"},
            }.get(ruta, {"email": "n@ejemplo.test"})


@pytest.mark.parametrize("ruta", ("/auth/login", RESET, RECUPERAR, "/auth/register"))
def test_tabla_una_ip_larga_entra_en_la_clave(ruta):
    """La clave de la tabla tiene 120 caracteres: una IP más larga no puede
    llegar tal cual (en Postgres el INSERT falla y la ruta da 500). Los largos
    dejan la clave, con su prefijo, entre 121 y 300 caracteres y por encima."""
    for largo in (115, 200, 287, 332):
        ip = ("x" * largo + uuid.uuid4().hex)[-largo:]
        r = TestClient(app).post(ruta, json=_cuerpo_auth(ruta), headers=_xff(ip))
        assert r.status_code in (200, 401), (largo, r.status_code, r.text)
        assert _claves_largas() == [], largo


def test_s4_una_ip_larga_tambien_se_bloquea():
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    real, c = _ip_larga(), TestClient(app)
    codigos = [_login(c, "nadie", "x", real).status_code for _ in range(6)]
    assert codigos == [401] * 5 + [429], codigos


def test_s4_dos_ips_largas_con_el_mismo_comienzo_no_se_pisan():
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    una, otra, c = _ip_larga(), _ip_larga(), TestClient(app)
    for _ in range(6):
        _login(c, "nadie", "x", una)
    r = _login(c, "nadie", "x", otra)
    assert r.status_code == 401, (r.status_code, r.text)


@pytest.mark.parametrize("ruta,cuerpo,pasa", [
    (RECUPERAR, b'{"email": "a\\ud800@ejemplo.test"}', 200),
    (RESET, b'{"email": "a\\udfff\\u0000@ejemplo.test"}', 200),
    ("/auth/login", b'{"username": "a\\ud800", "password": "x"}', 401),
])
@pytest.mark.parametrize("limitador", (True, False))
def test_un_surrogate_suelto_no_da_500(ruta, cuerpo, pasa, limitador):
    """JSON acepta «\\ud800» sin su par y «\\u0000»; ese texto no se puede
    codificar ni guardar en Postgres, y la ruta daba 500. Ahora responde como a
    un dato que no existe."""
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = limitador
    r = TestClient(app, raise_server_exceptions=False).post(
        ruta, content=cuerpo, headers={"Content-Type": "application/json", **_xff(_ip())})
    assert r.status_code == pasa, (r.status_code, r.text[:200])
