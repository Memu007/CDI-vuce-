"""Los casos de tests/test_admin_usuarios1.py contra un Postgres de verdad: la lista
de usuarios del panel, sembrada y leída por otra conexión en Postgres.

Corre cada caso del archivo con sus parámetros. Fuera de pytest la app no tiene el
atajo de sesión de las pruebas, así que «sin sesión» pasa por el camino real, y el
LIKE es el de Postgres, sin el que lo imita en SQLite.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases y ser superusuario, para apagar la clave foránea al
dejar a una usuaria en un estudio que no existe):
  python scripts/testing/admin_usuarios1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
o con uno que se levanta y se borra:
  PY=venv/bin/python scripts/testing/con_pg16.sh sh -c \
    '"$PY" scripts/testing/admin_usuarios1_postgres.py "$BACKUP1A_PG_URL"'
"""
import asyncio
import functools
import inspect
import os
import subprocess
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: admin_usuarios1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"admin_usuarios1_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", NCM_GEMINI_FALLBACK="false",
)
os.environ.pop("PYTEST_CURRENT_TEST", None)
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

import psycopg2  # noqa: E402

FALLAS = []


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


def casos(modulo, fijas):
    """Cada test_ del módulo, una vez por juego de parámetros; lo demás que pide sale de fijas.
    Sabe leer un parametrize de dos o más nombres, con listas de ids y de tuplas de ese largo, nada
    más: ante otra marca se corta antes de correr."""
    if getattr(modulo, "pytestmark", None):
        sys.exit("el módulo tiene marcas que este guion no sabe correr")
    lista = []
    for nombre, caso in vars(modulo).items():
        if not nombre.startswith("test_") or not inspect.isfunction(caso):
            continue
        marcas = getattr(caso, "pytestmark", [])
        juegos = [(nombre, {})]
        if marcas:
            marca = marcas[0]
            nombres, valores = (marca.args + (None, None))[:2]
            ids = marca.kwargs.get("ids")
            claves = [c.strip() for c in nombres.split(",")] if type(nombres) is str else []
            if (len(marcas) > 1 or marca.name != "parametrize" or len(marca.args) != 2
                    or set(marca.kwargs) != {"ids"}
                    or len(claves) < 2 or type(valores) is not list or type(ids) is not list
                    or not valores or len(ids) != len(valores)
                    or any(type(v) is not tuple or len(v) != len(claves) for v in valores)):
                sys.exit(f"{nombre}: tiene marcas que este guion no sabe correr")
            juegos = [(f"{nombre}[{id_}]", dict(zip(claves, v))) for id_, v in zip(ids, valores)]
        for id_, dados in juegos:
            argumentos = {p: dados[p] if p in dados else fijas[p] for p in inspect.signature(caso).parameters}
            lista.append((id_, functools.partial(caso, **argumentos)))
    return lista


def recogidos(archivo):
    """Lo que pytest junta del archivo, con su conftest y en SQLite: lo que el guion tiene que correr."""
    entorno = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "ENVIRONMENT")}
    # Sin el addopts de pytest.ini (-v, cobertura): -q deja un id por renglón.
    salida = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "--collect-only", "-q",
                             "-p", "no:cacheprovider", archivo], cwd=RAIZ, env=entorno, capture_output=True, text=True)
    if salida.returncode:
        sys.exit(f"pytest no pudo juntar {archivo}:\n{salida.stdout[-2000:]}")
    return {linea.split("::", 1)[1] for linea in salida.stdout.splitlines() if linea.startswith(f"{archivo}::")}


try:
    de_pytest = recogidos("tests/test_admin_usuarios1.py")
    admin(f'create database "{BASE}"')
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
    from sqlalchemy.pool import NullPool  # noqa: E402
    import proyecto_maria.database.connection as conexion  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    # Sin pool, como en tests/conftest.py: cada asyncio.run y cada TestClient tienen su loop, y
    # una conexión de asyncpg queda atada al loop donde nació.
    conexion.engine = create_async_engine(conexion.DATABASE_URL, poolclass=NullPool)
    conexion.AsyncSessionLocal = async_sessionmaker(conexion.engine, expire_on_commit=False)
    import tests.test_admin_usuarios1 as caso_admin  # noqa: E402
    limiter.enabled = False
    asyncio.run(conexion.init_db())
    # Las fixtures de prueba no hacen falta acá: sin pytest no hay atajo ni LIKE que imitar.
    fijas = dict(sembradas=caso_admin._sembrar_cuentas(), sin_bypass_de_test=None, like_distingue_mayusculas=None)
    lista = casos(caso_admin, fijas)
    for id_, correr in lista:
        try:
            # Un caso async o generador devuelve algo sin haber corrido.
            devuelto = correr()
            chequear(devuelto is None, id_ if devuelto is None else f"{id_}: no corrió, devolvió {devuelto!r}")
        # Un sys.exit dentro de un caso no puede terminar el guion en verde.
        except (Exception, SystemExit) as e:
            chequear(False, f"{id_}: {type(e).__name__}: {str(e)[:600]}")
    corridos = {id_ for id_, _ in lista}
    chequear(corridos == de_pytest, f"el guion corrió {len(corridos)} casos y pytest junta {len(de_pytest)}; "
                                    f"sólo pytest: {sorted(de_pytest - corridos)}, sólo el guion: {sorted(corridos - de_pytest)}")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
