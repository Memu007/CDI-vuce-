"""ENTRADAS-3 contra un Postgres de verdad: lo que SQLite guarda sin quejarse y
Postgres no. tests/test_entradas3.py (que conftest ata a SQLite) no lo mide, y
bajo pytest el registro de pedidos no se escribe. Comprueba que:
1. un pedido con NUL en la ruta, o a una ruta de 300 caracteres que no existe,
   queda en api_logs como <sin ruta>; el de un molde de 300 caracteres queda
   recortado a 200, y el de una excepción con NUL en el mensaje también queda;
2. un número enorme en la operación manual o al guardar al cliente no se guarda,
   y el listado de clientes y las métricas del cliente siguen respondiendo;
3. un NUL en la consulta no da 500.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/entradas3_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import os
import sys
import time
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: entradas3_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"entradas3_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
os.environ.pop("PYTEST_CURRENT_TEST", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "Clave-sintetica-1!"
LARGA = "/x" * 150


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def admin(consulta, url=URL, parametros=None):
    con = psycopg2.connect(url)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta, parametros)
            return cur.fetchall() if cur.description else None
    finally:
        con.close()


def registrados(donde, parametros):
    return admin(f"select count(*) from api_logs where {donde}", URL_BASE, parametros)[0][0]


def esperar_registros(donde, parametros, cuantos, tope=15.0):
    # El registro se escribe en una tarea aparte: se espera a verlo, con un tope.
    hasta = time.monotonic() + tope
    while time.monotonic() < hasta:
        if registrados(donde, parametros) >= cuantos:
            return True
        time.sleep(0.05)
    return False


try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    limiter.enabled = False
    # Rutas sólo de esta prueba: un molde más largo que la columna y una
    # excepción con NUL en el mensaje, que por HTTP no se pueden pedir de otra forma.
    MOLDE_LARGO = "/api/e3-molde" + "/x" * 150
    main_mod.app.add_api_route(MOLDE_LARGO, lambda: {"ok": True})

    def _falla():
        raise RuntimeError("e3\x00falla")
    main_mod.app.add_api_route("/api/e3-falla", _falla)

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        def cuenta():
            u = "e3_" + uuid.uuid4().hex[:10]
            r = c.post("/auth/register", json={"username": u, "password": CLAVE,
                                               "email": f"{u}@example.com", "name": "E"})
            assert r.status_code == 200, r.text
            return {"Authorization": f"Bearer {r.json()['access_token']}"}

        def pedir(metodo, ruta, sesion, cuerpo):
            return c.request(metodo, ruta, content=cuerpo.encode(),
                             headers={**sesion, "Content-Type": "application/json"})

        sesion = cuenta()

        # 1. registro de pedidos
        sin_ruta = ("endpoint = '<sin ruta>' and status_code = 404", None)
        for nombre, ruta in [("NUL en la ruta", "/api/nul-a%00b"), ("ruta de 300 caracteres", LARGA)]:
            antes = registrados(*sin_ruta)
            r = c.get(ruta, headers=sesion)
            chequear(r.status_code < 500 and esperar_registros(*sin_ruta, antes + 1),
                     f"{nombre}: {r.status_code}; como <sin ruta>: {registrados(*sin_ruta) - antes}")
        camino = ("endpoint like '/api/nul-a%' or endpoint like '/x/x%'", None)
        chequear(registrados(*camino) == 0, f"el camino no queda en api_logs: {registrados(*camino)}")

        r = c.get(MOLDE_LARGO, headers=sesion)
        molde = ("endpoint = %s", (MOLDE_LARGO[:200],))
        chequear(r.status_code == 200 and esperar_registros(*molde, 1),
                 f"molde de 300 caracteres: {r.status_code}; recortado a 200: {registrados(*molde)}")

        r = c.get("/api/e3-falla", headers=sesion)
        falla = ("endpoint = '/api/e3-falla' and status_code = 500 and error_message = %s", ("e3\ufffdfalla",))
        chequear(r.status_code == 500 and esperar_registros(*falla, 1),
                 f"excepción con NUL en el mensaje: {r.status_code}; en api_logs: {registrados(*falla)}")

        # 2. números enormes y las sumas de total_value, cada uno en su cuenta
        for numero in ("1e308", "-1e308", "1e16"):
            sesion = cuenta()
            cid = pedir("POST", "/api/clientes", sesion, '{"nombre": "C"}').json()["cliente"]["id"]
            for _ in range(2):
                manual = pedir("POST", "/api/operations/manual", sesion,
                               f'{{"client_id": "{cid}", "items": [{{"descripcion": "D", "cantidad": 1, '
                               f'"valor_unitario": {numero}}}]}}')
                guardar = pedir("POST", f"/api/clientes/{cid}/operaciones", sesion,
                                f'{{"items": [], "resumen": {{"valor_total": {numero}}}}}')
                chequear(manual.status_code == 400 and guardar.status_code == 400,
                         f"{numero}: manual {manual.status_code}, guardar al cliente {guardar.status_code}")
            listado = c.get("/api/clientes", headers=sesion)
            metricas = c.get(f"/api/clientes/{cid}/metricas", headers=sesion)
            chequear(listado.status_code == 200 and metricas.status_code == 200,
                     f"después de {numero}: listado {listado.status_code}, métricas {metricas.status_code}")

        sesion = cuenta()
        cid = pedir("POST", "/api/clientes", sesion, '{"nombre": "Tope"}').json()["cliente"]["id"]
        for _ in range(3):
            r = pedir("POST", f"/api/clientes/{cid}/operaciones", sesion,
                      '{"items": [], "resumen": {"valor_total": 1e15}}')
            chequear(r.status_code == 200, f"guardar al cliente con el tope 1e15: {r.status_code} {r.text[:80]}")
        listado = c.get("/api/clientes", headers=sesion)
        metricas = c.get(f"/api/clientes/{cid}/metricas", headers=sesion)
        chequear(listado.status_code == 200 and metricas.status_code == 200,
                 f"tres operaciones en el tope suman sin reventar: listado {listado.status_code}, "
                 f"métricas {metricas.status_code}")

        # 3. NUL en la consulta
        r = c.get("/api/clientes/search?q=a%00b", headers=sesion)
        chequear(r.status_code == 400, f"NUL en la consulta: {r.status_code} {r.text[:80]}")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
