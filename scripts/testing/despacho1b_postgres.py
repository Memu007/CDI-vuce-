"""DESPACHO-1b contra un Postgres de verdad, partiendo de una base con el
esquema y los datos de la versión anterior (1f5480e por defecto), que no
tenía `clave` ni índice único en client_product_history.

1. Crea una base descartable en el servidor de la URL y arranca ahí la
   versión anterior (un worktree): registra un usuario, un cliente y aprende
   un producto. Se agregan por SQL, como filas que dejó esa versión, otra
   fila del mismo producto escrito de otra forma (NCM sin puntos, minúsculas,
   doble espacio y NFD) y una fila sin NCM válido.
2. Arranca la versión nueva sobre la misma base.

Comprueba:
- la migración une las dos filas del producto en la más reciente, suma los
  usos y pondera los promedios por sus usos, deja la fila sin NCM con la
  clave vacía y crea el índice único ux_cph_owner_client_clave;
- arrancar otra vez no cambia nada;
- dos procesos, cada uno con su conexión, guardan el despacho y aprenden el
  mismo producto escrito de dos formas a la vez: queda una fila con todos
  los usos y ningún pedido falla;
- dos aprendizajes a la vez con los mismos productos en orden contrario no
  se traban.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/despacho1b_postgres.py postgresql://cdi@127.0.0.1:55432/postgres [SHA anterior]
"""
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "1f5480e"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: despacho1b_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA]  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"despacho1b_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="despacho1b_pg_")
WT = os.path.join(TMP, "wt")

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "SecureP@ss1"
USUARIO = f"d1b{uuid.uuid4().hex[:6]}"
CANO = unicodedata.normalize("NFC", "CAÑO INVENTADO VERDE")
CANO_OTRA = unicodedata.normalize("NFD", "caño  inventado verde")


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
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", NCM_GEMINI_FALLBACK="false",
    )


def producto(ncm, descripcion, peso=0.1):
    return {"ncm": ncm, "descripcion": descripcion, "origen": "BR",
            "cantidad": 10, "valor_unitario": 2, "peso_unitario": peso}


# Lo que hace la versión anterior: crea su esquema, el usuario, el cliente y
# aprende un producto.
VIEJA = r'''
import json, sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave, item = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
with TestClient(m.app, raise_server_exceptions=False) as c:
    r = c.post("/auth/register", json={"username": usuario, "password": clave,
               "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    r = c.post("/api/clientes", json={"nombre": "Cliente DESPACHO1b sintetico"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    r = c.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [item]})
    assert r.status_code == 200, r.text
print("vieja ok " + cid)
'''

# Un proceso aparte, con su propia conexión, que manda `n` pedidos de a 4 a
# la vez apenas aparece el archivo de largada. Sin el arranque de la app.
PROCESO = r'''
import concurrent.futures, json, os, sys, time
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
token, url, cuerpo, n, largada = sys.argv[1], sys.argv[2], json.loads(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
# Con «with», un solo loop para todos los hilos: sin él, cada pedido abre un
# loop y las conexiones del pool quedan trabadas en el loop que las abrió.
with TestClient(m.app, raise_server_exceptions=False) as c:
    c.headers["Authorization"] = f"Bearer {token}"
    open(largada + ".listo." + str(os.getpid()), "w").close()
    while not os.path.exists(largada):
        time.sleep(0.01)
    with concurrent.futures.ThreadPoolExecutor(4) as ex:
        rs = list(ex.map(lambda _: c.post(url, json=cuerpo), range(n)))
print(json.dumps([[r.status_code, r.text[:200]] for r in rs]))
'''


def filas_de(cid):
    return sql("select ncm, descripcion, clave, veces_usado, peso_unitario_avg, veces_peso,"
               " valor_unitario_avg, veces_valor from client_product_history"
               " where client_id=%s order by ncm, descripcion", cid)


try:
    admin(f'create database "{BASE}"')
    py = sys.executable

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    r = subprocess.run([py, "-c", VIEJA, USUARIO, CLAVE, json.dumps(producto("3926.90.90", CANO))],
                       cwd=WT, env={**os.environ, **entorno(URL_BASE), "PYTHONPATH": WT},
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or "vieja ok" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-4000:])
        sys.exit("la versión anterior no arrancó o no aprendió el producto")
    CID = r.stdout.split("vieja ok ")[1].split()[0]
    cols = {c for (c,) in sql("select column_name from information_schema.columns "
                              "where table_name='client_product_history'")}
    chequear("clave" not in cols, f"la base de {ANTERIOR} no tiene clave")
    vieja = sql("select id from client_product_history where client_id=%s", CID)
    chequear(len(vieja) == 1, f"la versión anterior aprendió una fila: {vieja}")
    # Otra fila del mismo producto, de antes, con 3 usos de 0,4 kg y sin valor.
    sql("insert into client_product_history (id, owner_username, client_id, ncm, descripcion,"
        " descripcion_normalizada, peso_unitario_avg, origen_frecuente, valor_unitario_avg, veces_peso,"
        " veces_valor, veces_usado, primera_vez, ultima_vez) values"
        " (%s, %s, %s, '3926909000', %s, '', 0.4, 'BR', null, 3, 0, 3,"
        "  now() - interval '30 days', now() - interval '1 day')",
        str(uuid.uuid4()), USUARIO, CID, CANO_OTRA)
    sql("insert into client_product_history (id, owner_username, client_id, ncm, descripcion,"
        " veces_usado) values (%s, %s, %s, 'SIN-CLASIF', 'ALGO SIN NCM', 1)",
        str(uuid.uuid4()), USUARIO, CID)

    # --- 2. la versión nueva sobre la misma base
    os.environ.update(entorno(URL_BASE))
    sys.path.insert(0, REPO)
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    from proyecto_maria.database.connection import engine  # noqa: E402
    from proyecto_maria.services.client_memory import identidad_del_producto  # noqa: E402
    limiter.enabled = False

    class Arranque(TestClient):
        """Un arranque de la app; al salir cierra las conexiones, como un
        proceso que termina (cada arranque tiene su propio loop)."""
        def __exit__(self, *exc):
            self.portal.call(engine.dispose)
            return super().__exit__(*exc)

    clave_cano = identidad_del_producto("3926.90.90", CANO)[2]
    with Arranque(main_mod.app, raise_server_exceptions=False):
        pass
    unidas = filas_de(CID)
    redondeadas = [tuple(round(v, 9) if isinstance(v, float) else v for v in f) for f in unidas]
    # La fila que queda conserva su NCM y su descripción: sólo cambian la clave y las cuentas.
    chequear(redondeadas == [("3926.90.90", CANO, clave_cano, 4, 0.325, 4, 2.0, 1),
                             ("SIN-CLASIF", "ALGO SIN NCM", None, 1, None, None, None, None)],
             f"la migración une el producto en la fila más reciente, suma 4 usos y pondera el peso "
             f"(0,1×1 + 0,4×3)/4: {unidas}")
    indice = sql("select indexdef from pg_indexes where indexname='ux_cph_owner_client_clave'")
    chequear(indice == [("CREATE UNIQUE INDEX ux_cph_owner_client_clave ON public.client_product_history "
                         "USING btree (owner_username, client_id, clave)",)],
             f"crea el índice único: {indice}")
    with Arranque(main_mod.app, raise_server_exceptions=False):
        pass
    chequear(filas_de(CID) == unidas, f"arrancar otra vez no cambia nada: {filas_de(CID)}")

    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        r = c.post("/auth/login", json={"username": USUARIO, "password": CLAVE})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        c.cookies.clear()
        c.headers["Authorization"] = f"Bearer {token}"

        # Dos procesos a la vez: uno guarda el despacho y otro aprende, el
        # mismo producto escrito de dos formas.
        tapa, tapa_otra = "TAPA INVENTADA PG", unicodedata.normalize("NFD", "tapa  inventada pg")
        n = 8
        largada = os.path.join(TMP, "largada")
        pedidos = [
            (f"/api/clientes/{CID}/catalogo/despacho/guardar",
             {"renglones": [{"posicion_sim": "3926.90.90.000A", "descripcion": tapa, "origen": "BR",
                             "cantidad": 10.0, "valor_unitario": 2.0, "kilo_neto": 1.0}], "divisa": "USD"}),
            (f"/api/clientes/{CID}/catalogo/productos/learn",
             {"items": [producto("3926909000", tapa_otra)]}),
        ]
        # La salida va a un archivo: un caño lleno frena al proceso con la fila trabada.
        procesos = []
        try:
            # Uno arranca después del otro, y la largada cuando los dos esperan.
            for i, (url, cuerpo) in enumerate(pedidos):
                procesos.append(subprocess.Popen(
                    [py, "-c", PROCESO, token, url, json.dumps(cuerpo), str(n), largada],
                    cwd=REPO, env={**os.environ, "PYTHONPATH": REPO},
                    stdout=open(os.path.join(TMP, f"proceso_{i}.out"), "w"),
                    stderr=open(os.path.join(TMP, f"proceso_{i}.err"), "w")))
                listo = os.path.join(TMP, f"largada.listo.{procesos[-1].pid}")
                while not os.path.exists(listo) and procesos[-1].poll() is None:
                    time.sleep(0.01)
            open(largada, "w").close()
            for p in procesos:
                p.wait(timeout=300)
        finally:
            for p in procesos:
                if p.poll() is None:
                    p.kill()
        codigos = []
        for i, p in enumerate(procesos):
            if p.returncode != 0:
                print(open(os.path.join(TMP, f"proceso_{i}.err")).read()[-3000:])
                codigos.append("murió")
                continue
            salida = open(os.path.join(TMP, f"proceso_{i}.out")).read()
            codigos += [cod for cod, _ in json.loads(salida.strip().splitlines()[-1])]
        clave_tapa = identidad_del_producto("3926.90.90", tapa)[2]
        tapas = sql("select veces_usado from client_product_history where client_id=%s and clave=%s",
                    CID, clave_tapa)
        chequear(codigos == [200] * (2 * n) and tapas == [(2 * n,)],
                 f"dos procesos guardan y aprenden el mismo producto a la vez: una fila con {2 * n} usos: "
                 f"{sorted(set(map(str, codigos)))} {tapas}")

        # Dos aprendizajes a la vez con los mismos productos en orden contrario.
        items = [producto("8481.80.95", f"VALVULA INVENTADA {i}") for i in range(40)]
        for vuelta in range(3):
            with concurrent.futures.ThreadPoolExecutor(2) as ex:
                rs = list(ex.map(lambda orden: c.post(f"/api/clientes/{CID}/catalogo/productos/learn",
                                                      json={"items": orden}), (items, items[::-1])))
            chequear(sorted(r.status_code for r in rs) == [200, 200],
                     f"dos aprendizajes en orden contrario, vuelta {vuelta}: "
                     f"{sorted(r.status_code for r in rs)} {[r.text[:120] for r in rs if r.status_code != 200]}")
        valvulas = sql("select count(*), min(veces_usado), max(veces_usado) from client_product_history"
                       " where client_id=%s and descripcion like 'VALVULA INVENTADA %%'", CID)
        chequear(valvulas == [(40, 6, 6)], f"cada válvula, una fila con 6 usos: {valvulas}")
finally:
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")
    shutil.rmtree(TMP, ignore_errors=True)

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
