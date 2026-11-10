"""COBRO-CORTE-1 contra un Postgres de verdad (D6 a): SQLite serializa las
escrituras y no muestra la carrera.

Dos /generate_maria a la vez, con la fila de la cuenta bloqueada mientras se
mira el tope, se cuenta y se calcula el op_code:
1. con una operación libre en el plan, pasa una y la otra da 402 (tope);
2. con lugar, las dos cuentan y tienen op_code distinto;
3. dos regeneraciones distintas de una operación con nueve: una entra, la otra es
   otra operación y se cuenta;
4. dos miembros de un estudio con una libre: pasa uno (la cuenta es la org);
5. un id de operación con NUL o con un surrogate suelto es una operación nueva,
   al generar, al exportar y al guardar;
6. borrar un cliente espera el candado de la cuenta;
7. un guardado que esperaba detrás del borrado de su cliente da 404.

Para que la carrera pase de verdad, el primero que calcula su op_code (ya
contado, sin commit) o lee la operación que regenera espera a ver al otro: o el otro también llegó ahí (no
hubo lock) o Postgres lo muestra esperando un lock (pg_stat_activity). Si no
ve ninguna de las dos en 5 s, el caso no probó la carrera y falla.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/cobro_corte1_postgres.py postgresql://cdi@127.0.0.1:55432/cdi_prueba

La base tiene que estar vacía: el script crea las tablas.
"""
import asyncio
import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: cobro_corte1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

os.environ.update(
    DATABASE_URL=URL, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402
from tests.test_cobro_corte1 import _cliente, _generar, _guardar  # noqa: E402
from tests.test_maria7_rechazos_24_10 import _pedido  # noqa: E402

limiter.enabled = False
# Como EXPORT de test_maria1b_devolucion, que no se importa: su conftest cambia la base a SQLite.
EXPORTACION = dict(
    operation_id="FAC_PG5EXP", cuit_exportador="20111111112", exportador_nombre="EXPORTADORA DEMO",
    comprador_nombre="COMPRADOR DEMO", comprador_id="X1",
    items=[{"ncm": "84798999900H", "descripcion": "MAQUINA DEMO", "cantidad": 1,
            "valor_unitario": 5000, "peso_kg": 1220}],
)
CLAVE = "Clave-Inventada-123"
FALLAS = []


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def llega(condicion, segundos=5):
    fin = time.monotonic() + segundos
    while time.monotonic() < fin:
        if condicion():
            return True
        time.sleep(0.01)
    return False


def esperando_un_lock():
    return sql("""select count(*) from pg_stat_activity
                  where datname = current_database() and wait_event_type = 'Lock'""")[0][0]


# El primero que calcula su op_code o lee la operación espera a ver al otro (ver arriba).
LLEGADAS = []
VISTO = []
_op_code_original = main_mod._next_op_code


async def _esperar_al_otro():
    LLEGADAS.append(1)
    for _ in range(500):
        if len(LLEGADAS) >= 2:
            VISTO.append("llegaron los dos")
            break
        if await asyncio.to_thread(esperando_un_lock):
            VISTO.append("el otro espera el lock")
            break
        await asyncio.sleep(0.01)
    else:
        VISTO.append("nada")


async def _op_code_con_carrera(db, owner_username):
    codigo = await _op_code_original(db, owner_username)
    await _esperar_al_otro()
    return codigo


main_mod._next_op_code = _op_code_con_carrera
_operacion_original = main_mod._operacion_del_usuario


async def _operacion_con_carrera(db, username, operacion_id):
    """Con un operacion_id, el primero que lee la operación espera a ver al otro."""
    operacion = await _operacion_original(db, username, operacion_id)
    if operacion_id:
        await _esperar_al_otro()
    return operacion


main_mod._operacion_del_usuario = _operacion_con_carrera


def ops_de(tabla, campo, valor):
    return sql(f"select coalesce(ops_used_this_period, 0) from {tabla} where {campo} = %s", valor)[0][0]


def operaciones(usuario):
    return sql("""select op_code, generated_file from operations
                  where owner_username = %s order by op_code""", usuario)


with TestClient(main_mod.app) as c:

    def entrar(org=False):
        nombre = f"cc1pg_{uuid.uuid4().hex[:8]}"
        datos = {"username": nombre, "password": CLAVE, "email": f"{nombre}@cdi.test"}
        if org:
            r = c.post("/api/organizations/create", json={**datos, "name": f"Estudio {nombre}"})
        else:
            r = c.post("/auth/register", json={**datos, "name": nombre})
        assert r.status_code in (200, 201), r.text
        r = c.post("/auth/login", json={"username": nombre, "password": CLAVE})
        assert r.status_code == 200, r.text
        c.cookies.clear()
        return nombre, r.json()["access_token"]

    def a_la_vez(*pedidos):
        """Manda los pedidos (token, operation_id[, operacion_id, valor unitario]) a la vez
        y devuelve las respuestas en el mismo orden."""
        LLEGADAS.clear()
        VISTO.clear()

        def generar(pedido):
            token, operation_id, operacion_id, valor = (*pedido, "", None)[:4]
            cuerpo = _pedido()
            cuerpo["operation_id"] = operation_id
            cuerpo["operacion_id"] = operacion_id
            if valor:
                cuerpo["items"][0]["valor_unitario"] = valor
            return c.post("/generate_maria", json=cuerpo, headers={"Authorization": f"Bearer {token}"})

        with ThreadPoolExecutor(len(pedidos)) as hilos:
            return list(hilos.map(generar, pedidos))

    def hubo_carrera(que):
        chequear(VISTO[:1] in (["llegaron los dos"], ["el otro espera el lock"]),
                 f"{que}: los dos pedidos se cruzaron ({VISTO})")

    def code(r):
        detalle = r.json().get("detail") if r.status_code == 402 else None
        return detalle.get("code") if isinstance(detalle, dict) else None

    # 1. Una libre: pasa una.
    u, t = entrar()
    sql("update users set ops_used_this_period = 14 where username = %s", u)
    rs = a_la_vez((t, "FAC_PG1A"), (t, "FAC_PG1B"))
    hubo_carrera("tope")
    estados = sorted(r.status_code for r in rs)
    chequear(estados == [200, 402] and "PLAN_LIMIT_EXCEEDED" in [code(r) for r in rs],
             f"tope: con una libre pasa una y la otra da 402 por el tope ({[(r.status_code, code(r)) for r in rs]})")
    chequear(ops_de("users", "username", u) == 15 and len(operaciones(u)) == 1,
             f"tope: queda en 15 con una operación ({ops_de('users', 'username', u)}, {operaciones(u)})")

    # 2. Con lugar: op_code distinto.
    u, t = entrar()
    rs = a_la_vez((t, "FAC_PG2A"), (t, "FAC_PG2B"))
    hubo_carrera("op_code")
    codigos = [fila[0] for fila in operaciones(u)]
    chequear([r.status_code for r in rs] == [200, 200] and ops_de("users", "username", u) == 2
             and codigos == ["OP-000001", "OP-000002"],
             f"op_code: las dos cuentan con código distinto ({[r.status_code for r in rs]}, "
             f"{ops_de('users', 'username', u)}, {codigos})")

    # 3. Una operación con nueve contenidos y dos distintos a la vez: entra uno, el otro cuenta.
    u, t = entrar()
    r = c.post("/generate_maria", json={**_pedido(), "operation_id": "FAC_PG3"},
               headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200, r.text
    op = r.json()["operacion_id"]
    sql("update operations set extra = %s where id = %s",
        json.dumps({"maria_hashes": [f"h{i}" for i in range(9)]}), op)
    rs = a_la_vez((t, "FAC_PG3", op, 1.85), (t, "FAC_PG3", op, 1.95))
    hubo_carrera("mismo id")
    huellas = sql("select json_array_length(extra::json -> 'maria_hashes') from operations where id = %s", op)[0][0]
    devueltas = sorted(r.json().get("operacion_id") == op for r in rs if r.status_code == 200)
    chequear([r.status_code for r in rs] == [200, 200] and ops_de("users", "username", u) == 2
             and len(operaciones(u)) == 2 and huellas == 10 and devueltas == [False, True],
             f"mismo id: una entra con la décima, la otra es otra operación contada "
             f"({[r.status_code for r in rs]}, {ops_de('users', 'username', u)}, {len(operaciones(u))} operaciones, "
             f"{huellas} huellas)")

    # 4. Dos miembros del estudio con una libre: pasa uno.
    admin, t_admin = entrar(org=True)
    org = sql("select organization_id from users where username = %s", admin)[0][0]
    miembro, t_miembro = entrar()
    sql("update users set organization_id = %s where username = %s", org, miembro)
    sql("update organizations set ops_used_this_period = 14 where id = %s", org)
    rs = a_la_vez((t_admin, "FAC_PG4A"), (t_miembro, "FAC_PG4B"))
    hubo_carrera("estudio")
    chequear(sorted(r.status_code for r in rs) == [200, 402] and ops_de("organizations", "id", org) == 15,
             f"estudio: con una libre pasa un miembro ({[(r.status_code, code(r)) for r in rs]}, "
             f"org {ops_de('organizations', 'id', org)})")
    chequear(ops_de("users", "username", admin) == 0 and ops_de("users", "username", miembro) == 0,
             "estudio: los usuarios no cuentan, cuenta la organización")

    class ConToken:
        """Los ayudantes de test_cobro_corte1 con el token de una cuenta."""
        def __init__(self, token):
            self.h = {"Authorization": f"Bearer {token}"}

        def post(self, url, json):
            return c.post(url, json=json, headers=self.h)

    # 5. Un id que Postgres no acepta es una operación nueva, no un 500. Guardar
    # rechaza todo el cuerpo con medio par: no cuenta ni guarda nada.
    rutas = {
        "generar": lambda ct, oid: _generar(ct, operacion_id=oid),
        "exportar": lambda ct, oid: ct.post("/generate_maria_export", json={**EXPORTACION, "operacion_id": oid}),
        "guardar": lambda ct, oid: _guardar(ct, _cliente(ct), "MARIA_FAC_PG5.TXT", oid),
    }
    for ruta, enviar in rutas.items():
        for nombre, raro in (("NUL", "a\x00b"), ("surrogate", "a\ud800b")):
            u, t = entrar()
            r = enviar(ConToken(t), raro)
            rechazado = (ruta, nombre) == ("guardar", "surrogate")
            esperado = 0 if rechazado else 1
            chequear(r.status_code == (400 if rechazado else 200)
                     and ops_de("users", "username", u) == esperado and len(operaciones(u)) == esperado,
                     f"id con {nombre} al {ruta}: {'rechazado sin contar' if rechazado else 'una operación nueva y contada'} ({r.status_code}, "
                     f"{ops_de('users', 'username', u)}, {len(operaciones(u))} operaciones)")

    # 6. Borrar un cliente reescribe sus operaciones: espera el mismo candado que generar.
    u, t = entrar()
    cliente = _cliente(ConToken(t))
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute("select 1 from users where username = %s for update", (u,))
        with ThreadPoolExecutor(1) as hilo:
            borrado = hilo.submit(c.delete, f"/api/clientes/{cliente}", headers={"Authorization": f"Bearer {t}"})
            espero = llega(lambda: esperando_un_lock() or borrado.done())
            espero = espero and not borrado.done()
            con.rollback()
            r = borrado.result()
    chequear(espero and r.status_code == 200,
             f"borrar cliente: espera el candado de la cuenta (esperó {espero}, {r.status_code})")

    # 7. Un guardado que esperaba detrás del borrado de su cliente da 404, no un 500.
    u, t = entrar()
    cliente = _cliente(ConToken(t))
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute("select 1 from users where username = %s for update", (u,))
        with ThreadPoolExecutor(1) as hilo:
            guardado = hilo.submit(_guardar, ConToken(t), cliente, "MARIA_FAC_PG7.TXT")
            espero = llega(lambda: esperando_un_lock() or guardado.done())
            espero = espero and not guardado.done()
            cur.execute("delete from clients where id = %s", (cliente,))
            con.commit()
            r = guardado.result()
    chequear(espero and r.status_code == 404 and operaciones(u) == [],
             f"guardar en un cliente que se borró mientras esperaba: 404 sin operación "
             f"(esperó {espero}, {r.status_code}, {len(operaciones(u))} operaciones)")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
