"""ENTRADAS-2 contra un Postgres de verdad. En SQLite un NUL, un surrogate, un
NaN o un entero de más de 32 bits se guardan sin quejarse, así que
tests/test_entradas2.py (que conftest ata a SQLite) no lo mide. Comprueba que:
1. la operación manual con un número no finito, un texto no guardable o un
   grupo_id fuera de rango no da 500, y después la lista de operaciones sigue;
2. alta y edición de cliente con un texto no guardable no dan 500;
3. guardar una operación al cliente con NaN o infinito, también anidado, no da 500;
4. un NUL en un parámetro de ruta no da 500;
5. agrupar con más ítems de los que el driver acepta, o cuando el número de
   grupo siguiente no entra en la columna, no da 500;
6. el alta de estudio pide la misma clave que el registro.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/entradas2_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: entradas2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"entradas2_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "Clave-sintetica-1!"


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def admin(consulta, url=URL):
    con = psycopg2.connect(url)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
            return cur.fetchall() if cur.description else None
    finally:
        con.close()


try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    limiter.enabled = False

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        def cuenta():
            u = "e2_" + uuid.uuid4().hex[:10]
            r = c.post("/auth/register", json={"username": u, "password": CLAVE,
                                               "email": f"{u}@example.com", "name": "E"})
            assert r.status_code == 200, r.text
            return {"Authorization": f"Bearer {r.json()['access_token']}"}

        def pedir(metodo, ruta, sesion, cuerpo):
            # JSON tal cual: json= de httpx no deja mandar NaN ni un surrogate suelto.
            return c.request(metodo, ruta, content=cuerpo.encode("utf-8", "surrogatepass"),
                             headers={**sesion, "Content-Type": "application/json"})

        def cliente(sesion):
            r = c.post("/api/clientes", headers=sesion, json={"nombre": "C"})
            assert r.status_code == 200, r.text
            return r.json()["cliente"]["id"]

        # 1. operación manual
        for nombre, item in [
            ("cantidad NaN", '{"descripcion": "D", "cantidad": NaN, "valor_unitario": 1}'),
            ("cantidad 1e999", '{"descripcion": "D", "cantidad": 1e999, "valor_unitario": 1}'),
            ("valor_unitario -Infinity", '{"descripcion": "D", "cantidad": 1, "valor_unitario": -Infinity}'),
            ("cantidad de texto", '{"descripcion": "D", "cantidad": "abc"}'),
            ("ítem que no es objeto", '"D"'),
            ("NUL en descripcion", '{"descripcion": "D\\u0000x", "cantidad": 1}'),
            ("surrogate en pieza", '{"pieza": "P\\ud800", "descripcion": "D", "cantidad": 1}'),
            ("grupo_id 99999999999", '{"descripcion": "D", "cantidad": 1, "grupo_id": 99999999999}'),
        ]:
            sesion = cuenta()
            cid = cliente(sesion)
            r = pedir("POST", "/api/operations/manual", sesion, f'{{"client_id": "{cid}", "items": [{item}]}}')
            lista = c.get("/api/operations", headers=sesion).status_code
            hist = c.get(f"/api/clientes/{cid}/operaciones", headers=sesion).status_code
            chequear(r.status_code < 500 and lista == 200 and hist == 200,
                     f"manual, {nombre}: {r.status_code} {r.text[:80]}; después lista {lista}, historial {hist}")

        # 2. alta y edición de cliente
        sesion = cuenta()
        cid = cliente(sesion)
        for campo in ("nombre", "email", "telefono", "cuit", "direccion", "notas"):
            for que, texto in (("NUL", "\\u0000"), ("surrogate", "\\ud800")):
                cuerpo = f'{{"nombre": "C", "{campo}": "x{texto}y"}}'
                alta = pedir("POST", "/api/clientes", sesion, cuerpo)
                edicion = pedir("PUT", f"/api/clientes/{cid}", sesion, f'{{"{campo}": "x{texto}y"}}')
                chequear(alta.status_code < 500 and edicion.status_code < 500,
                         f"cliente.{campo} con {que}: alta {alta.status_code} {alta.text[:60]}; "
                         f"edición {edicion.status_code} {edicion.text[:60]}")

        # 3. guardar operación al cliente
        for nombre, cuerpo in [
            ("NaN en items", '{"items": [{"descripcion": "D", "cantidad": NaN}]}'),
            ("NaN en resumen", '{"items": [], "resumen": {"valor_total": NaN}}'),
            ("NaN anidado en resumen", '{"items": [], "resumen": {"a": [[1, NaN]]}}'),
            ("1e999 en resumen", '{"items": [], "resumen": {"a": 1e999}}'),
            ("resumen.items de texto", '{"items": [], "resumen": {"items": "abc"}}'),
            ("surrogate en descripcion", '{"items": [{"descripcion": "D\\ud800"}]}'),
        ]:
            sesion = cuenta()
            cid = cliente(sesion)
            r = pedir("POST", f"/api/clientes/{cid}/operaciones", sesion, cuerpo)
            hist = c.get(f"/api/clientes/{cid}/operaciones", headers=sesion).status_code
            chequear(r.status_code < 500 and hist == 200,
                     f"guardar al cliente, {nombre}: {r.status_code} {r.text[:80]}; después historial {hist}")

        # 4. NUL en la ruta
        sesion = cuenta()
        for metodo, ruta, cuerpo in [
            ("GET", "/api/invitations/a%00b", None),
            ("GET", "/api/clientes/a%00b", None),
            ("POST", "/api/operacion/a%00b/agrupar", '{"item_ids": ["a", "b"]}'),
            ("POST", "/api/operacion/a%00b/desagrupar", '{"grupo_id": 1}'),
        ]:
            r = pedir(metodo, ruta, sesion, cuerpo or "")
            chequear(r.status_code < 500, f"NUL en {metodo} {ruta}: {r.status_code} {r.text[:80]}")

        # 5. agrupar con más ítems que los parámetros del driver
        r = c.post("/api/operacion/no-existe/agrupar", headers=sesion,
                   json={"item_ids": [str(i) for i in range(40000)]})
        chequear(r.status_code < 500, f"agrupar con 40000 ítems: {r.status_code} {r.text[:80]}")
        tope = '{"descripcion": "Tope", "cantidad": 1, "grupo_id": 2147483647}'
        libres = '{"descripcion": "A", "cantidad": 1}, {"descripcion": "B", "cantidad": 1}'
        r = pedir("POST", "/api/operations/manual", sesion,
                  f'{{"client_id": "{cliente(sesion)}", "items": [{tope}, {libres}]}}')
        op_id = r.json().get("operation_id", "")
        ids = [fila[0] for fila in admin(
            f"select id from operation_items where operation_id = '{op_id}' and grupo_id is null", URL_BASE)]
        r = c.post(f"/api/operacion/{op_id}/agrupar", headers=sesion, json={"item_ids": ids})
        chequear(r.status_code == 409 and len(ids) == 2,
                 f"agrupar con el grupo 2147483647 ocupado: {r.status_code} {r.text[:80]}")

        # 6. clave del alta de estudio
        u = "e2_" + uuid.uuid4().hex[:10]
        r = c.post("/api/organizations/create", json={"name": "Estudio", "username": u,
                                                      "password": "abcdefgh", "email": f"{u}@example.com"})
        chequear(r.status_code == 400, f"estudio con clave sólo de letras: {r.status_code} {r.text[:80]}")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
