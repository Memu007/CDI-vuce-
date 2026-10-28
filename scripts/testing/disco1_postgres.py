"""DISCO-1 contra un Postgres de verdad, partiendo de una base que ya tiene
el esquema y los datos de la versión anterior (c996ad4 por defecto), como
la de producción la primera vez que arranca la versión nueva.

1. Crea una base descartable en el servidor de la URL y arranca ahí la
   versión anterior (un worktree): crea sus tablas, registra usuarios, un
   cliente y confirma NCM, que esa versión escribe en archivos de DATA_DIR.
   Se agregan a mano un archivo roto, uno con una cuenta que no entra en un
   entero de Postgres y uno con nombre ambiguo. El alta no acepta «.» en el
   usuario, así que el segundo dueño del nombre ambiguo se copia por SQL,
   como un usuario de antes de esa validación.
2. Arranca la versión nueva sobre la misma base y el mismo DATA_DIR.

Comprueba:
- crea `ncm_historial` con su clave única y su clave foránea, y las demás
  tablas conservan sus filas;
- carga cada archivo a su dueño con sus cuentas y lo renombra a `.migrado`;
  el roto, el de cuenta enorme y el ambiguo quedan en su lugar y van al log,
  sin frenar a los demás ni el arranque;
- sugerir devuelve lo cargado, confirmar suma uno y actualiza la NCM;
  un dueño no ve ni pisa el historial de otro;
- confirmaciones a la vez no pierden cuentas (contra Postgres, no SQLite);
- un NUL o un texto de más da 400, no 500, y no guarda nada;
- importar 7000 filas entra en tandas, y dos importaciones a la vez con las
  mismas filas en orden contrario no se traban;
- importar y cargar archivos viejos toman el bloqueo de su dueño: la carga
  espera a una importación del mismo dueño, y las de otro dueño no esperan;
- arrancar otra vez, aunque vuelva un archivo, no duplica cuentas;
- borrar DATA_DIR no borra el historial.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/disco1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres [SHA anterior]
"""
import concurrent.futures
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "c996ad4"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: disco1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA]  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"disco1_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="disco1_pg_")
DATA_DIR = os.path.join(TMP, "data")
WT = os.path.join(TMP, "wt")
os.makedirs(DATA_DIR)

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "SecureP@ss1"
SUF = uuid.uuid4().hex[:6]
# Los archivos se cargan en orden de nombre: el de cuenta enorme va antes que
# uno bueno, para ver que no frena a los que siguen.
A, B, C = f"dp{SUF}_1a", f"dp{SUF}_3b", f"dp{SUF}_4c"
ENORME, ROTO = f"dp{SUF}_2enorme", f"dp{SUF}_0roto"
PUNTO, GUION = f"dp{SUF}.amb", f"dp{SUF}_amb"


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def admin(consulta):
    con = psycopg2.connect(URL)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
    finally:
        con.close()


def sql(consulta, *args):
    with psycopg2.connect(URL_BASE) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def entorno(url):
    return dict(
        DATABASE_URL=url, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
        JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
        GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", CDI_DATA_DIR=DATA_DIR,
        NCM_GEMINI_FALLBACK="false",
    )


# Lo que hace la versión anterior: crea su esquema y escribe historial en archivos.
VIEJA = r'''
import json, os, sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuarios, clave = json.loads(sys.argv[1]), sys.argv[2]
with TestClient(m.app, raise_server_exceptions=False) as c:
    for u in usuarios:
        c.cookies.clear()
        r = c.post("/auth/register", json={"username": u, "password": clave,
                   "email": f"{u.replace('.', '-')}@example.com", "name": u})
        assert r.status_code == 200, r.text
        if u.endswith("_1a"):
            r = c.post("/api/clientes", json={"nombre": "Cliente DISCO1 sintetico"})
            assert r.status_code == 200, r.text
            for ncm in ("8413.70.10", "8413.70.90"):
                r = c.post("/api/ncm/guardar-uso", json={"descripcion": "Bomba sintetica", "ncm": ncm})
                assert r.status_code == 200 and r.json()["success"], r.text
            r = c.post("/api/ncm/guardar-uso", json={"descripcion": "Valvula sintetica", "ncm": "8481.80.95"})
            assert r.status_code == 200, r.text
        if u.endswith("_4c"):
            r = c.post("/api/ncm/guardar-uso", json={"descripcion": "Junta sintetica", "ncm": "4016.93.00"})
            assert r.status_code == 200, r.text
print("vieja ok")
'''

# La carga de archivos viejos del arranque, sola, en un proceso aparte.
CARGAR = r'''
import asyncio
import proyecto_maria.main as m
asyncio.run(m._migrate_ncm_historial_archivos())
'''


def archivo(owner_seguro, contenido):
    ruta = os.path.join(DATA_DIR, f"ncm_historial_{owner_seguro}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido if isinstance(contenido, str) else json.dumps(contenido))
    return ruta


def filas(owner):
    return sql("select descripcion, ncm, count from ncm_historial where owner_username=%s order by id", owner)


def conteos():
    tablas = [t for (t,) in sql(
        "select table_name from information_schema.tables where table_schema='public' "
        "and table_type='BASE TABLE' and table_name <> 'ncm_historial' order by 1")]
    return {t: sql(f'select count(*) from "{t}"')[0][0] for t in tablas}


try:
    admin(f'create database "{BASE}"')
    py = sys.executable

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    r = subprocess.run([py, "-c", VIEJA, json.dumps([A, B, C, ENORME, ROTO, GUION]), CLAVE],
                       cwd=WT, env={**os.environ, **entorno(URL_BASE), "PYTHONPATH": WT},
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or "vieja ok" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-4000:])
        sys.exit("la versión anterior no arrancó o no guardó el historial")
    chequear(sql("select to_regclass('ncm_historial')")[0][0] is None,
             f"la base de {ANTERIOR} no tiene ncm_historial")
    chequear(sorted(os.listdir(DATA_DIR)) == sorted([f"ncm_historial_{A}.json", f"ncm_historial_{C}.json"]),
             f"la versión anterior escribió el historial en archivos: {sorted(os.listdir(DATA_DIR))}")
    cols = [c for (c,) in sql("select column_name from information_schema.columns "
                              "where table_schema='public' and table_name='users' order by ordinal_position")]
    origen = ", ".join({"username": "%s", "email": "null"}.get(c, f'"{c}"') for c in cols)
    sql(f'insert into users ({", ".join(chr(34) + c + chr(34) for c in cols)}) '
        f'select {origen} from users where username=%s', PUNTO, GUION)
    archivo(ROTO, '{"Bomba": {"ncm": "8413')
    archivo(ENORME, {"Tuerca sintetica": {"ncm": "7318.16.00", "count": 2 ** 40}})
    archivo(f"dp{SUF}_amb", {"Llave sintetica": {"ncm": "8481.80.99", "count": 1}})
    antes = conteos()

    # --- 2. la versión nueva sobre la misma base
    os.environ.update(entorno(URL_BASE))
    sys.path.insert(0, REPO)
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    from proyecto_maria.database.connection import engine  # noqa: E402
    limiter.enabled = False

    class Arranque(TestClient):
        """Un arranque de la app; al salir cierra las conexiones, como un
        proceso que termina (cada arranque tiene su propio loop)."""
        def __exit__(self, *exc):
            self.portal.call(engine.dispose)
            return super().__exit__(*exc)

    class Log(logging.Handler):
        def __init__(self):
            super().__init__(logging.WARNING)
            self.textos = []

        def emit(self, rec):
            self.textos.append(rec.getMessage())
    log = Log()
    logging.getLogger().addHandler(log)

    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        chequear(sql("select to_regclass('ncm_historial')")[0][0] == "ncm_historial", "el arranque crea ncm_historial")
        restr = {(t, cols) for t, cols in sql(
            "select contype, pg_get_constraintdef(oid) from pg_constraint "
            "where conrelid='ncm_historial'::regclass and contype in ('u','f')")}
        chequear(("u", "UNIQUE (owner_username, clave)") in restr
                 and ("f", "FOREIGN KEY (owner_username) REFERENCES users(username)") in restr,
                 f"clave única por dueño y descripción, y clave foránea a users: {sorted(restr)}")
        # Sólo las que ya estaban: la versión nueva puede crear otras vacías.
        despues = conteos()
        chequear({t: despues.get(t) for t in antes} == antes, "las demás tablas conservan sus filas: "
                 f"{ {t: (n, despues.get(t)) for t, n in antes.items() if despues.get(t) != n} }")

        chequear(filas(A) == [("Bomba sintetica", "8413.70.90", 2), ("Valvula sintetica", "8481.80.95", 1)],
                 f"el archivo de A se cargó con sus cuentas: {filas(A)}")
        chequear(filas(C) == [("Junta sintetica", "4016.93.00", 1)],
                 f"el de C, que va después del de cuenta enorme, también: {filas(C)}")
        chequear(filas(ENORME) == [] and filas(ROTO) == [] and filas(PUNTO) == [] and filas(GUION) == [],
                 "el de cuenta enorme, el roto y el ambiguo no se le cargan a nadie")
        quedan = sorted(os.listdir(DATA_DIR))
        chequear(quedan == sorted([f"ncm_historial_{A}.json.migrado", f"ncm_historial_{C}.json.migrado",
                                   f"ncm_historial_{ROTO}.json", f"ncm_historial_{ENORME}.json",
                                   f"ncm_historial_dp{SUF}_amb.json"]),
                 f"lo cargado queda como .migrado y lo demás en su lugar: {quedan}")
        textos = "\n".join(log.textos)
        chequear(all(f"ncm_historial_{n}.json" in textos for n in (ROTO, ENORME, f"dp{SUF}_amb")),
                 "el roto, el de cuenta enorme y el ambiguo van al log")
        chequear("Tuerca" not in textos and "Bomba" not in textos and "Llave" not in textos,
                 "el log no copia descripciones")

        def entrar(u):
            c.cookies.clear()
            r = c.post("/auth/login", json={"username": u, "password": CLAVE})
            assert r.status_code == 200, r.text

        def del_historial(desc):
            r = c.post("/api/ncm/sugerir", json={"descripcion": desc})
            assert r.status_code == 200, r.text
            return [(s["ncm"], s.get("count")) for s in r.json()["sugerencias"] if s["source"] == "historial"]

        entrar(A)
        chequear(del_historial("Bomba sintetica") == [("8413.70.90", 2)], "sugerir devuelve lo cargado")
        r = c.post("/api/ncm/guardar-uso", json={"descripcion": "Bomba sintetica", "ncm": "8413.70.99"})
        chequear(r.status_code == 200 and filas(A)[0] == ("Bomba sintetica", "8413.70.99", 3),
                 f"confirmar suma uno y actualiza la NCM: {filas(A)[0]}")

        entrar(B)
        chequear(del_historial("Bomba sintetica") == [], "B no ve el historial de A")
        c.post("/api/ncm/guardar-uso", json={"descripcion": "Bomba sintetica", "ncm": "8413.11.00"})
        r = c.post("/api/ncm/import-historial", files={"file": (
            "h.csv", b"descripcion,ncm\nBomba sintetica,8413.19.00\nPolea sintetica,8483.50.10\n", "text/csv")})
        chequear(r.status_code == 200 and r.json()["importados"] == 1 and r.json()["duplicados"] == 1,
                 f"importar en Postgres cuenta igual: {r.status_code} {r.text[:160]}")
        chequear(filas(B) == [("Bomba sintetica", "84131900", 1), ("Polea sintetica", "84835010", 1)],
                 f"lo de B: {filas(B)}")
        chequear(filas(A)[0] == ("Bomba sintetica", "8413.70.99", 3), "B no pisó lo de A")

        # Confirmaciones a la vez, cada una en su conexión de Postgres.
        entrar(A)
        n = 16
        with concurrent.futures.ThreadPoolExecutor(n) as ex:
            rs = list(ex.map(lambda _: c.post("/api/ncm/guardar-uso", json={
                "descripcion": "Rodamiento sintetico", "ncm": "8482.10.10"}), range(n)))
        chequear(all(r.status_code == 200 for r in rs) and ("Rodamiento sintetico", "8482.10.10", n) in filas(A),
                 f"{n} confirmaciones a la vez cuentan {n}: {[r.status_code for r in rs if r.status_code != 200]} "
                 f"{[f for f in filas(A) if f[0] == 'Rodamiento sintetico']}")

        # Si falla la memoria del cliente o la del proveedor, sugerir sigue
        # con lo demás: en Postgres, un error atrapado sin rollback deja la
        # transacción abortada y el historial se perdía sin aviso.
        cliente = sql("select id from clients where owner_username=%s", A)[0][0]
        prov = "Proveedor DISCO1 sintetico"
        r = c.post("/api/ncm/guardar-uso", json={"descripcion": "Compresor sintetico", "ncm": "8414.80.11",
                                                 "client_id": cliente, "vendor_name": prov})
        chequear(r.status_code == 200, f"confirmar con cliente y proveedor: {r.status_code} {r.text[:160]}")

        def fuentes(**extra):
            r = c.post("/api/ncm/sugerir", json={"descripcion": "Compresor sintetico", **extra})
            assert r.status_code == 200, r.text
            return [(s["source"], s.get("scope")) for s in r.json()["sugerencias"]]
        chequear(fuentes(client_id=cliente, vendor_name=prov) == [("historial", "cliente")],
                 f"con todo sano, la del cliente: {fuentes(client_id=cliente, vendor_name=prov)}")

        def con_columna_rota(tabla, columna, que):
            sql(f"alter table {tabla} rename column {columna} to roto_disco1")
            try:
                return que()
            finally:
                sql(f"alter table {tabla} rename column roto_disco1 to {columna}")
        f = con_columna_rota("client_product_history", "descripcion_normalizada",
                             lambda: fuentes(client_id=cliente))
        chequear(f == [("historial", None)], f"falla la memoria del cliente: sigue el historial: {f}")
        f = con_columna_rota("vendor_catalog_products", "product_key", lambda: fuentes(vendor_name=prov))
        chequear(f == [("historial", None)], f"falla el catálogo del proveedor: sigue el historial: {f}")
        f = con_columna_rota("client_product_history", "descripcion_normalizada",
                             lambda: fuentes(client_id=cliente, vendor_name=prov))
        chequear(f == [("proveedor", "proveedor")], f"falla la memoria del cliente: sigue el proveedor: {f}")

        # Un NUL o una descripción de más: 400 claro, no 500 de la base.
        antes_a = filas(A)
        for desc, ncm, que in (("Bomba\x00sintetica", "8413.70.10", "un NUL en la descripción"),
                               ("Bomba sintetica", "8413.70.10\x00", "un NUL en la NCM"),
                               ("B" * 2001, "8413.70.10", "una descripción de 2001 caracteres")):
            r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": ncm})
            chequear(r.status_code == 400, f"{que} da 400: {r.status_code} {r.text[:160]}")
        chequear(filas(A) == antes_a, "y no se guarda nada")
        r = c.post("/api/ncm/guardar-uso", json={"descripcion": "Bomba sintetica", "ncm": "8413.70.10",
                                                 "client_id": "cliente\x00sintetico"})
        chequear(r.status_code == 400 and filas(A) == antes_a,
                 f"un NUL en el cliente da 400 y no suma: {r.status_code} {r.text[:160]}")

        # Muchas filas: en tandas, por debajo del tope de parámetros de asyncpg.
        entrar(B)
        n = 7000
        csv = "descripcion,ncm\n" + "".join(f"Pieza sintetica {i},8481.80.95\n" for i in range(n))
        r = c.post("/api/ncm/import-historial", files={"file": ("h.csv", csv.encode(), "text/csv")})
        chequear(r.status_code == 200 and len(filas(B)) == n + 2,
                 f"importar {n} filas en Postgres: {r.status_code} {r.text[:160]} {len(filas(B))}")

        # Dos importaciones a la vez con las mismas filas en orden contrario:
        # sin el bloqueo por dueño se trababan (deadlock) y una daba 500.
        descs = [f"Pieza sintetica {i}" for i in range(1000)]
        def importar(orden):
            csv = "descripcion,ncm\n" + "".join(f"{d},8413.19.00\n" for d in orden)
            return c.post("/api/ncm/import-historial", files={"file": ("h.csv", csv.encode(), "text/csv")})
        for vuelta in range(3):
            with concurrent.futures.ThreadPoolExecutor(2) as ex:
                rs = list(ex.map(importar, (descs, descs[::-1])))
            # Los códigos ordenados: cuál de las dos pierde cambia de una vuelta a otra.
            chequear([r.status_code for r in rs] == [200, 200],
                     f"dos importaciones a la vez en orden contrario, vuelta {vuelta}: "
                     f"{sorted(r.status_code for r in rs)} {[r.text[:120] for r in rs]}")

        # Cada camino que escribe el historial en tandas (importar y la carga
        # de archivos viejos) toma el bloqueo de su dueño, y el de otro dueño
        # no lo espera. Una importación de A queda a mitad de camino con su
        # bloqueo tomado: otra conexión tiene sin confirmar una fila que esa
        # importación también escribe. Las sesiones van por Bearer, sin
        # cookie, para que cada pedido sea de su dueño aunque vayan a la vez.
        tokens = {}
        for u in (A, B):
            c.cookies.clear()
            r = c.post("/auth/login", json={"username": u, "password": CLAVE})
            tokens[u] = {"Authorization": f"Bearer {r.json()['access_token']}"}
        c.cookies.clear()

        def importar_de(u, descs):
            csv = "descripcion,ncm\n" + "".join(f"{d},8413.19.00\n" for d in descs)
            return c.post("/api/ncm/import-historial", headers=tokens[u],
                          files={"file": ("h.csv", csv.encode(), "text/csv")})

        def esperar(que, hasta=120):
            """Hasta que `que()` dé algo, o None si pasa `hasta` segundos."""
            fin = time.monotonic() + hasta
            while time.monotonic() < fin:
                r = que()
                if r:
                    return r
                time.sleep(0.05)
            return None

        def en_espera(tipo):
            # Sólo las esperas de esta base: pg_locks es de todo el servidor y
            # otra corrida en el mismo Postgres daría un «esperó» falso.
            return sql("select count(*) from pg_locks l join pg_stat_activity a using (pid)"
                       " where a.datname = current_database() and l.locktype = %s and not l.granted",
                       tipo)[0][0]

        def cargar_archivos():
            """La carga del arranque, en otro proceso con su propia conexión."""
            # La salida va a un archivo: un caño lleno también lo frenaría.
            salida = open(os.path.join(TMP, f"carga_{len(procesos)}.log"), "w")
            return subprocess.Popen([py, "-c", CARGAR], cwd=REPO, env={**os.environ, "PYTHONPATH": REPO},
                                    stdout=salida, stderr=subprocess.STDOUT)

        trabada = "Pieza sintetica trabada"
        de_a = [f"Pieza sintetica a{i}" for i in range(300)] + [trabada]
        tenedor = psycopg2.connect(URL_BASE)
        procesos = []
        ex = concurrent.futures.ThreadPoolExecutor(2)
        try:
            with tenedor.cursor() as cur:
                cur.execute("insert into ncm_historial (owner_username, clave, descripcion, ncm, count) "
                            "values (%s, %s, %s, '8413.19.00', 1)",
                            (A, hashlib.sha256(trabada.encode()).hexdigest(), trabada))
            imp_a = ex.submit(importar_de, A, de_a)
            chequear(esperar(lambda: en_espera("transactionid")) and not imp_a.done(),
                     "la importación de A queda esperando la fila sin confirmar, con su bloqueo tomado")

            # Otro dueño no espera: importa y carga su archivo viejo.
            imp_b = ex.submit(importar_de, B, [f"Pieza sintetica b{i}" for i in range(300)])
            fin_b = esperar(lambda: "terminó" if imp_b.done() else
                            ("esperó" if en_espera("advisory") else None))
            chequear(fin_b == "terminó" and imp_b.result().status_code == 200,
                     f"la importación de B no espera el bloqueo de A: {fin_b} "
                     f"{imp_b.result().status_code if imp_b.done() else ''}")
            archivo(B, {f"Arandela sintetica b{i}": {"ncm": "7318.22.00", "count": 2} for i in range(300)})
            carga = cargar_archivos()
            procesos.append(carga)
            fin_cb = esperar(lambda: "terminó" if carga.poll() is not None else
                             ("esperó" if en_espera("advisory") else None))
            chequear(fin_cb == "terminó" and carga.returncode == 0
                     and sum(1 for f in filas(B) if f[0].startswith("Arandela sintetica b")) == 300,
                     f"la carga del archivo de B no espera el bloqueo de A: {fin_cb} {carga.returncode}")

            # El mismo dueño sí espera: la carga de A queda en el bloqueo.
            archivo(A, {f"Arandela sintetica a{i}": {"ncm": "7318.22.00", "count": 2} for i in range(300)})
            carga = cargar_archivos()
            procesos.append(carga)
            fin_ca = esperar(lambda: "esperó" if en_espera("advisory") else
                             ("terminó" if carga.poll() is not None else None))
            chequear(fin_ca == "esperó" and carga.poll() is None and not imp_a.done(),
                     f"la carga del archivo de A espera a la importación de A: {fin_ca}")

            tenedor.rollback()
            r = imp_a.result(timeout=120)
            carga.wait(timeout=120)
            ya_a = {f[0] for f in filas(A)}
            chequear(r.status_code == 200 and carga.returncode == 0 and set(de_a) <= ya_a
                     and {f"Arandela sintetica a{i}" for i in range(300)} <= ya_a,
                     f"al soltarse, las dos de A terminan: {r.status_code} {carga.returncode} "
                     f"{len(set(de_a) - ya_a)} {len({f'Arandela sintetica a{i}' for i in range(300)} - ya_a)}")
        finally:
            # Primero se suelta la fila: si algo falló a mitad, lo que espera termina.
            tenedor.close()
            for p in procesos:
                if p.poll() is None:
                    p.kill()
            ex.shutdown(wait=True)

    # --- otro arranque, con el archivo de A de vuelta
    shutil.copy(os.path.join(DATA_DIR, f"ncm_historial_{A}.json.migrado"),
                os.path.join(DATA_DIR, f"ncm_historial_{A}.json"))
    antes_a = filas(A)
    with Arranque(main_mod.app, raise_server_exceptions=False):
        pass
    chequear(filas(A) == antes_a, f"arrancar otra vez con el archivo de vuelta no duplica ni pisa: {filas(A)}")

    # --- sin DATA_DIR
    shutil.rmtree(DATA_DIR)
    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        c.cookies.clear()
        r = c.post("/auth/login", json={"username": A, "password": CLAVE})
        r = c.post("/api/ncm/sugerir", json={"descripcion": "Bomba sintetica"})
        hist = [(s["ncm"], s.get("count")) for s in r.json()["sugerencias"] if s["source"] == "historial"]
        chequear(hist == [("8413.70.99", 3)], f"borrar DATA_DIR no borra el historial: {hist}")
finally:
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")
    shutil.rmtree(TMP, ignore_errors=True)

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
