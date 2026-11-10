"""CATALOGO-3 contra un Postgres de verdad: SQLite no controla el largo de
operation_items.origen ni tiene dos workers que migran a la vez.

1. Crea una base descartable y arranca ahí la versión anterior (un worktree,
   07504e0 por defecto): guarda una operación con origen «TAIWAN», dos
   productos de un proveedor sólo CJK («电线 2mm» y «钢管 2mm») y un
   producto de cada uno de dos proveedores largos con los mismos 60
   primeros caracteres.
2. Arranca dos veces a la vez la versión a probar (el repositorio, o la que
   diga el tercer argumento): las dos esperan juntas el candado de la
   migración y las dos tienen que arrancar.

Comprueba:
- que operation_items.origen pasa a text y la fila vieja queda como estaba;
- que una operación manual y una del historial del cliente guardan
  «TAIWAN» entero;
- que la migración le da al proveedor CJK un id no vacío, separa a los dos
  proveedores largos y no pierde ninguna fila;
- que «电线 2mm» y «钢管 2mm» quedan en dos filas;
- que un tercer arranque no cambia nada;
- que un worker arranca aunque otro tenga tomada más de 5 s la migración
  de las claves;
- que ante dos productos que empatan en parecido gana el texto idéntico y
  después el último confirmado, guardados en cualquier orden.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/catalogo3_postgres.py postgresql://cdi@127.0.0.1:<puerto>/postgres [SHA anterior] [carpeta a probar]
"""
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.parse import urlparse

import psycopg2

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "07504e0"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: catalogo3_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA] [carpeta]")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUEVA = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else REPO
BASE = f"catalogo3_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="catalogo3_pg_")
WT = os.path.join(TMP, "wt")
CANDADO = 7302551

FALLAS = []
USUARIO = f"c3{uuid.uuid4().hex[:6]}"
CLAVE = "SecureP@ss1"
CJK = "电线有限公司"
LARGOS = ("Proveedor de nombre muy largo " + "x" * 40 + " uno",
          "Proveedor de nombre muy largo " + "x" * 40 + " dos")
NCM = "73181500"

# Corre adentro de la carpeta de una versión: lo que guarda sale por el
# Postgres; imprime una línea JSON con lo que contestó.
GUARDAR = r'''
import json, sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave, cjk, largos, ncm, registrar = json.loads(sys.argv[1])
out = {}
with TestClient(m.app, raise_server_exceptions=False) as c:
    if registrar:
        r = c.post("/auth/register", json={"username": usuario, "password": clave,
                   "email": f"{usuario}@example.com", "name": usuario})
        assert r.status_code == 200, r.text
    else:
        assert c.post("/auth/login", json={"username": usuario, "password": clave}).status_code == 200
    r = c.post("/api/clientes", json={"nombre": "Cliente sintetico " + usuario})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    item = {"descripcion": "TUERCA", "cantidad": 1, "valor_unitario": 1, "peso_unitario": 1,
            "pieza": ncm, "origen": "TAIWAN"}
    r = c.post("/api/operations/manual", json={"client_id": cid, "items": [item]})
    out["manual"] = [r.status_code, r.json().get("operation_id")]
    r = c.post(f"/api/clientes/{cid}/operaciones", json={"items": [item]})
    out["historial"] = [r.status_code, r.text[:200]]
    for desc in ("电线 2mm", "钢管 2mm"):
        r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": ncm, "vendor_name": cjk})
        out[desc] = r.status_code
    for nombre, desc in zip(largos, ("TORNILLO", "ARANDELA")):
        r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": ncm, "vendor_name": nombre})
        out[desc] = r.status_code
print("GUARDADO " + json.dumps(out))
'''

# Dos textos que empatan en parecido, guardados en un orden y en el otro, y el
# mismo texto con dos NCM confirmados A, B, A: imprime qué NCM sugiere cada vez.
EMPATAR = r'''
import json, sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave, a, b = json.loads(sys.argv[1])
pares = [("Cable 2,5mm²", "Cable 2,5mm2"), ("Bolt Ｍ８", "Bolt M8"), ("Capacitor 10µF", "Capacitor 10μF")]
out = {"identico": [], "ultima": []}
with TestClient(m.app, raise_server_exceptions=False) as c:
    assert c.post("/auth/login", json={"username": usuario, "password": clave}).status_code == 200
    def cliente():
        return c.post("/api/clientes", json={"nombre": "Cliente sintetico"}).json()["cliente"]["id"]
    def confirmar(cid, desc, ncm):
        c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": ncm, "vendor_name": "P", "client_id": cid})
    def sugiere(cid, desc):
        r = c.post("/api/catalog/lookup", json={"items": [{"descripcion": desc}], "vendor_name": "Otro", "client_id": cid})
        return r.json()["items"][0]["ncm"]
    for x, y in pares:
        for guardados in ([(x, a), (y, b)], [(y, b), (x, a)]):
            cid = cliente()
            for desc, ncm in guardados:
                confirmar(cid, desc, ncm)
            out["identico"].append([sugiere(cid, x), sugiere(cid, y)])
    for x, y, buscado in [("Cable 2,5mm2",) * 3, ("Cable 2,5mm²", "Cable 2,5mm2", "CABLE 2,5MM2")]:
        cid = cliente()
        vistos = []
        for desc, ncm in [(x, a), (y, b), (x, a)]:
            confirmar(cid, desc, ncm)
            vistos.append(sugiere(cid, buscado))
        out["ultima"].append(vistos)
print("EMPATES " + json.dumps(out))
'''

ARRANCAR = r'''
from fastapi.testclient import TestClient
import proyecto_maria.main as m
with TestClient(m.app, raise_server_exceptions=False):
    print("ARRANCO")
'''


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args, base=None):
    with contextlib.closing(psycopg2.connect(base or URL_BASE)) as con, con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def entorno():
    return {**os.environ, "DATABASE_URL": URL_BASE, "ENVIRONMENT": "testing",
            "EMAIL_VERIFICATION_REQUIRED": "false", "GEMINI_API_KEY": "test-key",
            "JWT_SECRET_KEY": "clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
            "VUCE_MODE": "fake", "TARIFAR_MODE": "fake", "AFIP_MODE": "fake",
            "DOLARAPI_BASE": "http://127.0.0.1:9/v1/dolares", "NCM_GEMINI_FALLBACK": "false"}


def correr(carpeta, codigo, *args):
    return subprocess.Popen([sys.executable, "-c", codigo, *args], cwd=carpeta,
                            env={**entorno(), "PYTHONPATH": carpeta},
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def guardar(carpeta, registrar):
    p = correr(carpeta, GUARDAR, json.dumps([USUARIO, CLAVE, CJK, LARGOS, NCM, registrar]))
    salida, error = p.communicate(timeout=600)
    if "GUARDADO " not in salida:
        print(salida[-2000:], error[-4000:])
        sys.exit(f"la versión de {carpeta} no guardó")
    return json.loads(salida.split("GUARDADO ")[1].splitlines()[0]), salida


def tipo_origen():
    return sql("select data_type, character_maximum_length from information_schema.columns"
               " where table_name='operation_items' and column_name='origen'")[0]


def catalogo():
    return sql("select vendor_id, vendor_nombre, product_key, descripcion from vendor_catalog_products"
               " where owner_username=%s order by descripcion", USUARIO)


def esperando_candado(n):
    hasta = time.monotonic() + 120
    while time.monotonic() < hasta:
        if sql("select count(*) from pg_locks where locktype='advisory' and objid=%s and not granted",
               CANDADO)[0][0] >= n:
            return True
        time.sleep(0.05)
    return False


try:
    con = psycopg2.connect(URL)
    con.autocommit = True
    con.cursor().execute(f'create database "{BASE}"')
    con.close()

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    vieja, _ = guardar(WT, True)
    filas_viejas = catalogo()
    item_viejo = sql("select origen from operation_items")
    print("anterior:", vieja, tipo_origen(), item_viejo, filas_viejas)

    # --- 2. dos arranques a la vez de la versión a probar
    tomado = psycopg2.connect(URL_BASE)
    tomado.autocommit = True
    tomado.cursor().execute("select pg_advisory_lock(%s)", (CANDADO,))
    workers = [correr(NUEVA, ARRANCAR) for _ in range(2)]
    juntos = esperando_candado(2)
    tomado.close()
    salidas = [w.communicate(timeout=600) for w in workers]
    anduvieron = [w.returncode == 0 and "ARRANCO" in s for w, (s, _) in zip(workers, salidas)]
    for s, e in salidas:
        if "ARRANCO" not in s:
            print(s[-1500:], e[-3000:])
    chequear(juntos and all(anduvieron),
             f"dos workers esperan juntos la migración y arrancan los dos: juntos {juntos}, {anduvieron}")
    chequear(tipo_origen() == ("text", None) and sql("select origen from operation_items") == item_viejo,
             f"operation_items.origen pasa a text y la fila vieja queda igual: {tipo_origen()} "
             f"{sql('select origen from operation_items')}")

    filas = catalogo()
    sys.path.insert(0, NUEVA)
    from proyecto_maria.core import catalog_service as cs  # noqa: E402
    esperadas = sorted((cs._vendor_key(n), n, cs.clave_de_producto(d), d) for _, n, _, d in filas_viejas)
    ids_largos = {v for v, n, _, _ in filas if n in LARGOS}
    chequear(len(filas) == len(filas_viejas) and sorted(filas) == esperadas
             and all(v for v, _, _, _ in filas) and len(ids_largos) == 2,
             f"la migración da el proveedor y la clave de hoy sin perder filas: {filas}")

    # --- 3. la versión a probar guarda
    nueva, _ = guardar(NUEVA, False)
    origenes = sorted(o for o, in sql("select origen from operation_items"))
    chequear(nueva["manual"][0] == 200 and nueva["historial"][0] == 200
             and origenes.count("TAIWAN") == 2,
             f"la operación manual y la del historial guardan «TAIWAN» entero: {nueva} {origenes}")
    cjk = [d for v, _, _, d in catalogo() if v == cs._vendor_key(CJK)]
    chequear(sorted(cjk) == ["电线 2mm", "钢管 2mm"],
             f"«电线 2mm» y «钢管 2mm» del proveedor CJK quedan en dos filas: {cjk}")

    # --- 4. otro arranque no cambia nada
    antes = (tipo_origen(), catalogo(), sql("select origen from operation_items order by origen"))
    s, e = correr(NUEVA, ARRANCAR).communicate(timeout=600)
    cambios = [linea for linea in s.splitlines() if "Migracion" in linea and ("TEXT" in linea or "catálogo" in linea)]
    chequear("ARRANCO" in s and not cambios
             and antes == (tipo_origen(), catalogo(), sql("select origen from operation_items order by origen")),
             f"un tercer arranque no cambia nada: {cambios}")

    # --- 5. un worker arranca aunque otro siga más de 5 s con las claves del catálogo
    tomado = psycopg2.connect(URL_BASE)
    tomado.autocommit = True
    tomado.cursor().execute("select pg_advisory_lock(%s)", (CANDADO,))
    s, e = correr(NUEVA, ARRANCAR).communicate(timeout=600)
    tomado.close()
    chequear("ARRANCO" in s, "un worker arranca mientras otro tiene tomada la migración de claves: "
             + (e.strip().splitlines() or [""])[-1][:200])

    # --- 6. un empate no depende del orden de las filas
    OTRO = "84714900"
    s, e = correr(NUEVA, EMPATAR, json.dumps([USUARIO, CLAVE, NCM, OTRO])).communicate(timeout=600)
    empates = json.loads(s.split("EMPATES ")[1].splitlines()[0]) if "EMPATES " in s else e[-1500:]
    chequear(isinstance(empates, dict) and empates["identico"] == [[NCM, OTRO]] * 6,
             f"ante un empate gana el texto idéntico, en los dos órdenes de guardado: {empates}")
    chequear(isinstance(empates, dict) and empates["ultima"] == [[NCM, OTRO, NCM]] * 2,
             f"ante un empate sin texto idéntico gana la última confirmada: {empates}")
finally:
    with contextlib.suppress(Exception):
        con = psycopg2.connect(URL)
        con.autocommit = True
        con.cursor().execute(f'drop database if exists "{BASE}" with (force)')
        con.close()
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    shutil.rmtree(TMP, ignore_errors=True)

print(f"\n{len(FALLAS)} fallas" if FALLAS else "\ntodo OK")
sys.exit(1 if FALLAS else 0)
