"""CATALOGO-LARGO-2 contra un Postgres de verdad: SQLite no controla el largo
de las columnas y el corte no se ve.

1. Crea una base descartable en el servidor de la URL y arranca ahí la
   versión anterior (un worktree, 93cbdef por defecto): registra un usuario,
   un cliente y guarda en el catálogo un producto con origen «CN» y tres con
   clave latina a los que después les cambia la descripción por CJK, emoji y
   la mezcla de los dos.
2. Arranca la versión nueva sobre la misma base: una con la tabla tomada por
   otra conexión, una con escrituras en curso sobre las dos tablas y dos
   sin.

Comprueba:
- que con la tabla tomada el arranque falla en vez de seguir con el corte;
- que una escritura que traba la memoria del cliente y después el catálogo,
  como guardar-uso, no se traba con el arranque: andan los dos, y el log
  dice «pasa a TEXT» sólo de lo que quedó guardado;
- que origen y vendor_nombre del catálogo y el origen de la memoria del
  cliente pasan a text y la fila vieja queda igual, y que arrancar otra vez
  no cambia nada;
- que el origen «TAIWAN» y un proveedor de 220 caracteres se guardan enteros
  por el catálogo, por cambiar el origen y por guardar-uso con y sin cliente,
  y que guardar-uso con un cliente guarda también el origen entero en la
  memoria del cliente;
- que guardar-uso de «螺丝» con proveedor y sin cliente guarda la fila;
- que un carácter nulo, medio par UTF-16, null o false en el proveedor, la
  descripción o el origen no dan 500 por el lote, guardar-uso ni el cambio:
  un 200 guarda lo bueno y un 400 trae un motivo legible y no escribe nada;
- que la versión nueva guarda las descripciones CJK de la fila vieja en esa
  misma fila, y que la fila sigue editable;
- que 2000 caracteres CJK distintos se guardan por el catálogo, por
  guardar-uso y por cambiar la descripción: la clave entra en el índice único.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/catalogo_largo2_postgres.py postgresql://cdi@127.0.0.1:<puerto>/postgres [SHA anterior]
"""
import asyncio
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from urllib.parse import quote, urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "93cbdef"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: catalogo_largo2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA]  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"catalogo_largo2_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="catalogo_largo2_pg_")
WT = os.path.join(TMP, "wt")

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "SecureP@ss1"
USUARIO = f"cl2{uuid.uuid4().hex[:6]}"
VENDOR = "Proveedor sintetico"
VENDOR_ID = "proveedor_sintetico"
LARGO = "Proveedor largo " + "x" * 204
LARGO_ID = ("proveedor_largo_" + "x" * 204)[:60]
NCM = "73181500"
# Variados: repetidos, Postgres los comprime y entran en el índice igual.
CJK_LARGO = "".join(chr(0x4E00 + i * 7) for i in range(2000))
# La versión anterior les dejó la clave latina al cambiarles la descripción.
VIEJAS = (("VIEJO CJK", "螺丝钉"), ("VIEJO EMOJI", "🔩🔩"), ("VIEJO MEZCLA", "螺丝🔩"))
MALOS = {"nulo": "x\x00", "medio par": "x\ud800", "null": None, "false": False}


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
    # El with de psycopg2 cierra la transacción, no la conexión.
    with contextlib.closing(psycopg2.connect(URL_BASE)) as con, con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall()


def entorno(url):
    return dict(
        DATABASE_URL=url, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
        JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
        GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", NCM_GEMINI_FALLBACK="false",
    )


def columnas():
    return sql("select column_name, data_type, character_maximum_length from information_schema.columns"
               " where (table_name='vendor_catalog_products' and column_name in ('ncm','origen','vendor_nombre'))"
               " or (table_name='client_product_history' and column_name='origen_frecuente')"
               " order by column_name")


def esperar(consulta, *args):
    """Hasta que la consulta devuelve algo (60 s como mucho)."""
    hasta = time.monotonic() + 60
    while time.monotonic() < hasta:
        if sql(consulta, *args):
            return True
        time.sleep(0.01)
    return False


def legible(r):
    detalle = r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None
    return isinstance(detalle, str) and not any(p in detalle.lower() for p in ("codec", "surrogate", "\\u"))


def fila(vendor_id, descripcion):
    return sql("select vendor_nombre, ncm, origen from vendor_catalog_products where owner_username=%s"
               " and vendor_id=%s and descripcion=%s", USUARIO, vendor_id, descripcion)


VIEJA = r'''
import json
import sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave, vendor, vendor_id, ncm = sys.argv[1:6]
viejas = json.loads(sys.argv[6])
with TestClient(m.app, raise_server_exceptions=False) as c:
    r = c.post("/auth/register", json={"username": usuario, "password": clave,
               "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    r = c.post("/api/clientes", json={"nombre": "Cliente CATALOGO-LARGO-2 sintetico"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    r = c.post(f"/api/catalog/{vendor_id}/productos", json={"vendor_name": vendor,
               "productos": [{"descripcion": "TORNILLO", "ncm": ncm, "origen": "CN"}]})
    assert r.status_code == 200, r.text
    for vieja, nueva in viejas:
        r = c.post(f"/api/catalog/{vendor_id}/productos", json={"vendor_name": vendor,
                   "productos": [{"descripcion": vieja, "ncm": ncm}]})
        assert r.status_code == 200, r.text
        r = c.put(f"/api/catalog/{vendor_id}/productos/{vieja.lower()}", json={"descripcion_original": nueva})
        assert r.status_code == 200, r.text
print("vieja ok " + cid)
'''

try:
    admin(f'create database "{BASE}"')

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    r = subprocess.run([sys.executable, "-c", VIEJA, USUARIO, CLAVE, VENDOR, VENDOR_ID, NCM,
                        json.dumps(VIEJAS)],
                       cwd=WT, env={**os.environ, **entorno(URL_BASE), "PYTHONPATH": WT},
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or "vieja ok" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-4000:])
        sys.exit("la versión anterior no arrancó o no guardó el producto")
    CID = r.stdout.split("vieja ok ")[1].split()[0]
    viejo = fila(VENDOR_ID, "TORNILLO")
    claves_viejas = sql("select descripcion, product_key from vendor_catalog_products where descripcion in %s"
                        " order by descripcion", tuple(n for _, n in VIEJAS))
    chequear(columnas() == [("ncm", "character varying", 20), ("origen", "character varying", 5), ("origen_frecuente", "character varying", 3),
                            ("vendor_nombre", "character varying", 200)]
             and viejo == [(VENDOR, NCM, "CN")]
             and sorted(k for _, k in claves_viejas) == sorted(v.lower() for v, _ in VIEJAS),
             f"la base de {ANTERIOR} tiene las columnas cortas, el producto viejo y las claves latinas: "
             f"{columnas()} {viejo} {claves_viejas}")

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

    tomada = psycopg2.connect(URL_BASE)
    try:
        # Postgres suelta la tabla a los 30 s: sin el tope del arranque, éste
        # termina con las columnas migradas en vez de colgar la prueba.
        tomada.cursor().execute("set idle_in_transaction_session_timeout = '30s'; "
                                "select 1 from vendor_catalog_products limit 1")
        try:
            with Arranque(main_mod.app, raise_server_exceptions=False):
                arranco = True
        except Exception:
            arranco = False
            asyncio.run(engine.dispose(close=False))
    finally:
        tomada.close()
    chequear(not arranco and {t for _, t, _ in columnas()} == {"character varying"},
             f"con la tabla tomada el arranque falla en vez de seguir con las columnas cortas: {columnas()}")

    # Guardar-uso traba la memoria del cliente y después el catálogo.
    escritura = psycopg2.connect(URL_BASE)
    salida, arranque = io.StringIO(), {}

    def arrancar():
        try:
            with Arranque(main_mod.app, raise_server_exceptions=False):
                arranque["fin"] = "anduvo"
        except Exception as e:
            arranque["fin"] = repr(e)[:200]
            asyncio.run(engine.dispose(close=False))
    try:
        cur = escritura.cursor()
        cur.execute("set lock_timeout = '20s'")
        cur.execute("lock table client_product_history in row exclusive mode")
        with contextlib.redirect_stdout(salida):
            hilo = threading.Thread(target=arrancar)
            hilo.start()
            en_cola = esperar("select 1 from pg_stat_activity where datname=%s and wait_event_type='Lock'"
                              " and query ilike 'alter table client_product_history%%'", BASE)
            try:
                cur.execute("lock table vendor_catalog_products in row exclusive mode")
                escritura.commit()
                la_escritura = "anduvo"
            except Exception as e:
                escritura.rollback()
                la_escritura = repr(e)[:200]
            hilo.join(120)
    finally:
        escritura.close()
    tipos = {c: t for c, t, _ in columnas()}
    columna_de = {"vendor_catalog_products": ("ncm", "origen", "vendor_nombre"),
                  "client_product_history": ("origen_frecuente",)}
    mentiras = [linea for linea in salida.getvalue().splitlines() if "pasa a TEXT" in linea
                and any(c in linea and tipos.get(c) != "text" for t in columna_de for c in columna_de[t]
                        if t in linea)]
    print(salida.getvalue().strip())
    chequear(en_cola and arranque.get("fin") == "anduvo" and la_escritura == "anduvo" and not mentiras,
             f"el arranque y una escritura como guardar-uso andan los dos: en cola {en_cola}, arranque "
             f"{arranque.get('fin')}, escritura {la_escritura}, log que no quedó guardado {mentiras}")

    for vez in ("primer", "segundo"):
        with Arranque(main_mod.app, raise_server_exceptions=False):
            pass
        chequear(columnas() == [("ncm", "text", None), ("origen", "text", None), ("origen_frecuente", "text", None),
                                ("vendor_nombre", "text", None)]
                 and fila(VENDOR_ID, "TORNILLO") == viejo,
                 f"{vez} arranque: las columnas son text y el producto viejo queda igual: {columnas()}")

    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        r = c.post("/auth/login", json={"username": USUARIO, "password": CLAVE})
        chequear(r.status_code == 200, f"login ({r.status_code})")

        r = c.post(f"/api/catalog/{LARGO_ID}/productos", json={"vendor_name": LARGO, "productos": [
            {"descripcion": "TUERCA", "ncm": NCM, "origen": "TAIWAN"}]})
        chequear(r.status_code == 200 and fila(LARGO_ID, "TUERCA") == [(LARGO, NCM, "TAIWAN")],
                 f"el catálogo guarda enteros el origen y el proveedor: {r.status_code} {r.text[:120]}")

        r = c.put(f"/api/catalog/{VENDOR_ID}/productos/tornillo", json={"origen": "TAIWAN"})
        chequear(r.status_code == 200 and fila(VENDOR_ID, "TORNILLO") == [(VENDOR, NCM, "TAIWAN")],
                 f"cambiar el origen lo guarda entero: {r.status_code} {r.text[:120]}")

        for desc, cliente in (("ARANDELA", {}), ("BULON", {"client_id": CID})):
            r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": NCM, "vendor_name": LARGO,
                                                     "origen": "TAIWAN", **cliente})
            memoria = sql("select origen_frecuente from client_product_history where client_id=%s"
                          " and descripcion=%s", CID, desc)
            chequear(r.status_code == 200 and r.json() == {"success": True, "historial_guardado": True}
                     and fila(LARGO_ID, desc) == [(LARGO, NCM, "TAIWAN")]
                     and memoria == [("TAIWAN",)] * len(cliente),
                     f"guardar-uso {'con' if cliente else 'sin'} cliente guarda enteros el origen y el "
                     f"proveedor: {r.status_code} {r.text[:120]} memoria del cliente {memoria}")

        r = c.post("/api/ncm/guardar-uso", json={"descripcion": "螺丝", "ncm": NCM, "vendor_name": VENDOR})
        chequear(r.status_code == 200 and r.json() == {"success": True, "historial_guardado": True}
                 and fila(VENDOR_ID, "螺丝") == [(VENDOR, NCM, None)],
                 f"guardar-uso de «螺丝» sin cliente guarda la fila: {r.status_code} {r.text[:120]}")

        url = f"/api/catalog/{VENDOR_ID}/productos"
        for vieja, nueva in VIEJAS:
            r = c.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": nueva, "ncm": NCM}]})
            claves = [k for k, in sql("select product_key from vendor_catalog_products where owner_username=%s"
                                      " and vendor_id=%s and descripcion=%s", USUARIO, VENDOR_ID, nueva)]
            cambios = [c.put(f"{url}/{quote(k, safe='')}", json={"origen": "CN"}).status_code for k in claves]
            chequear(r.status_code == 200 and len(claves) == 1 and cambios == [200],
                     f"«{nueva}» de una fila vieja es una sola fila y sigue editable: {r.status_code}, "
                     f"claves {claves}, cambios {cambios}")

        def escrito(desc):
            return sql("select vendor_nombre, origen from vendor_catalog_products where owner_username=%s"
                       " and descripcion=%s union all select null, origen_frecuente from client_product_history"
                       " where descripcion=%s", USUARIO, desc, desc)

        def sano(filas):
            return bool(filas) and not any(v in ("None", "False") for f in filas for v in f)

        def mandar(metodo, ruta, cuerpo):
            return c.request(metodo, ruta, content=json.dumps(cuerpo), headers={"content-type": "application/json"})

        for via in ("lote", "guardar-uso", "cambio"):
            fallas = []
            for campo in ("proveedor", "descripción", "origen"):
                for nombre, valor in MALOS.items():
                    if via == "cambio" and campo == "proveedor":
                        continue
                    bueno = f"BUENO {via} {campo} {nombre}"
                    if isinstance(valor, str):  # único por caso: si no, el texto limpio choca con el de otro caso
                        valor = valor.replace("x", "x " + bueno, 1)
                    clave = {"proveedor": "vendor_name", "descripción": "descripcion"}.get(campo, campo)
                    if via == "lote":
                        malo = {"descripcion": "MALO " + bueno, "ncm": NCM, "origen": "CN"}
                        cuerpo = {"vendor_name": VENDOR, "productos": [{"descripcion": bueno, "ncm": NCM}, malo]}
                        (cuerpo if campo == "proveedor" else malo)[clave] = valor
                        r = mandar("POST", url, cuerpo)
                        guardo = r.status_code == 200 and sano(escrito(bueno))
                        intacto = not escrito(bueno)
                    elif via == "guardar-uso" and campo == "descripción":
                        r = mandar("POST", "/api/ncm/guardar-uso", {"descripcion": valor, "ncm": NCM,
                                                                    "vendor_name": bueno, "client_id": CID})
                        guardo = r.status_code == 200 and not escrito("None") and not escrito("False")
                        intacto = True
                    elif via == "guardar-uso":
                        cuerpo = {"descripcion": bueno, "ncm": NCM, "vendor_name": VENDOR, "origen": "CN",
                                  "client_id": CID, clave: valor}
                        r = mandar("POST", "/api/ncm/guardar-uso", cuerpo)
                        guardo = r.status_code == 200 and r.json().get("historial_guardado") is True \
                            and sano(escrito(bueno))
                        intacto = not escrito(bueno)
                    else:
                        mandar("POST", url, {"vendor_name": VENDOR,
                                             "productos": [{"descripcion": bueno, "ncm": NCM, "origen": "CN"}]})
                        fila_id, k = sql("select id, product_key from vendor_catalog_products where owner_username=%s"
                                         " and descripcion=%s", USUARIO, bueno)[0]
                        por_id = ("select vendor_nombre, ncm, origen, descripcion from vendor_catalog_products"
                                  " where id=%s")
                        antes = sql(por_id, fila_id)
                        r = mandar("PUT", f"{url}/{quote(k, safe='')}",
                                   {"descripcion_original" if campo == "descripción" else "origen": valor})
                        despues = sql(por_id, fila_id)
                        guardo = r.status_code == 200 and len(despues) == 1 and sano(despues)
                        intacto = despues == antes
                    if not (guardo or (r.status_code == 400 and legible(r) and intacto)):
                        fallas.append(f"{campo} {nombre}: {r.status_code} {r.text[:80]}")
            chequear(not fallas, f"una entrada mala por {via} no da 500 ni pierde lo bueno: {fallas}")

        # Un NCM más largo que la columna vieja, y precios que no son finitos: la lectura del
        # catálogo arma JSON estricto, así que lo guardado tiene que poder leerse después.
        fallas = []
        for i, (campo, valor) in enumerate((("ncm", "7" * 21), ("valor_unitario", "nan"), ("valor_unitario", "inf"),
                                            ("valor_unitario", float("inf")), ("valor_unitario", float("nan")),
                                            ("valor_unitario", 10 ** 400))):
            bueno = f"BUENO raro {i}"
            r = mandar("POST", url, {"vendor_name": VENDOR, "productos": [
                {"descripcion": bueno, "ncm": NCM}, {"descripcion": "MALO " + bueno, "ncm": NCM, campo: valor}]})
            k = sql("select product_key from vendor_catalog_products where owner_username=%s and descripcion=%s",
                    USUARIO, bueno)
            cambio = mandar("PUT", f"{url}/{quote(k[0][0], safe='')}",
                            {"precio_ref" if campo == "valor_unitario" else campo: valor}) if k else None
            lectura = c.get(f"/api/catalog/{VENDOR_ID}")
            if not (r.status_code in (200, 400) and k and cambio.status_code in (200, 400)
                    and lectura.status_code == 200):
                fallas.append(f"{campo} {str(valor)[:20]}: lote {r.status_code}, guardó lo bueno {bool(k)}, cambio "
                              f"{cambio.status_code if cambio else '-'}, lectura {lectura.status_code}")
        chequear(not fallas, f"un NCM largo o un precio no finito no da 500 ni rompe la lectura: {fallas}")

        for via, desc in (("catálogo", CJK_LARGO[:-1] + "一"), ("guardar-uso", CJK_LARGO[1:] + "一"),
                          ("cambiar la descripción", CJK_LARGO)):
            if via == "catálogo":
                r = c.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": desc, "ncm": NCM}]})
            elif via == "guardar-uso":
                r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": NCM, "vendor_name": VENDOR})
            else:
                r = c.put(f"{url}/tornillo", json={"descripcion_original": desc})
            chequear(r.status_code == 200 and len(fila(VENDOR_ID, desc)) == 1,
                     f"2000 caracteres CJK por {via} se guardan: {r.status_code} {r.text[:120]}")
finally:
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")
    shutil.rmtree(TMP, ignore_errors=True)

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
