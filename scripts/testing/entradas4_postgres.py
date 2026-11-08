"""ENTRADAS-4 contra un Postgres de verdad: un NUL en un campo de formulario de
texto no da 500. SQLite lo acepta y Postgres no, así que tests/ no lo mide.
Comprueba que:
1. los campos `Form` de texto de la app son los de CAMPOS (uno nuevo hace fallar
   hasta que se agrega acá);
2. cada uno, con un NUL, responde sin 500.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/entradas4_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import io
import os
import sys
import typing
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: entradas4_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"entradas4_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
os.environ.pop("PYTEST_CURRENT_TEST", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import openpyxl  # noqa: E402
import psycopg2  # noqa: E402
from fastapi.params import Form  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402

FALLAS = []
CLAVE = "Clave-sintetica-1!"
NUL = "a\x00b"


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


def excel_sintetico():
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(["Descripcion", "Cantidad", "Precio Unitario", "NCM"])
    hoja.append(["Tornillo sintetico", 10, 1.5, "7318.15.00"])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# (ruta, campo) -> los demás campos que la ruta necesita para llegar a usarlo.
CAMPOS = {
    ("/upload_excel_v2/", "cliente_id"): {"files": {"file": ("items.xlsx", excel_sintetico(), XLSX)}},
}


def es_texto(tipo):
    if typing.get_origin(tipo) is typing.Annotated:
        return es_texto(typing.get_args(tipo)[0])
    return tipo is str or any(es_texto(t) for t in typing.get_args(tipo))


def campos_form_de_texto(app):
    for ruta in app.routes:
        if not isinstance(ruta, APIRoute):
            continue
        for campo in ruta.dependant.body_params:
            if isinstance(campo.field_info, Form) and es_texto(campo.field_info.annotation):
                yield ruta.path, campo.alias


try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    limiter.enabled = False

    encontrados = set(campos_form_de_texto(main_mod.app))
    chequear(encontrados == set(CAMPOS), f"campos Form de texto: {sorted(encontrados)}")

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        u = "e4_" + uuid.uuid4().hex[:10]
        r = c.post("/auth/register", json={"username": u, "password": CLAVE,
                                           "email": f"{u}@example.com", "name": "E"})
        assert r.status_code == 200, r.text
        sesion = {"Authorization": f"Bearer {r.json()['access_token']}"}
        for (ruta, campo), resto in CAMPOS.items():
            r = c.post(ruta, headers=sesion, data={campo: NUL}, **resto)
            chequear(r.status_code < 500, f"NUL en {campo} de {ruta}: {r.status_code} {r.text[:80]}")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
