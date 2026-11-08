"""BACKUP-1a: la copia de la base se restaura y queda igual, o el script lo dice.

Necesitan un Postgres 16 local: `scripts/testing/con_pg16.sh` levanta uno
descartable, con clave, y deja su dirección en BACKUP1A_PG_URL. Sin esa
variable se saltean (la CI no tiene Postgres).

    PY=venv/bin/python scripts/testing/con_pg16.sh venv/bin/python -m pytest -q --no-cov tests/test_backup1a.py
"""
import asyncio
import datetime as dt
import hashlib
import json
import os
import secrets
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "scripts" / "datos" / "copia_base.py"
PG_URL = os.environ.get("BACKUP1A_PG_URL", "")
PG_BIN = os.environ.get("PG16_BIN", "/usr/lib/postgresql/16/bin")
FILAS = 3

pytestmark = pytest.mark.skipif(
    not PG_URL, reason="sin Postgres 16 local: correr con scripts/testing/con_pg16.sh")

if PG_URL and urlsplit(PG_URL).hostname not in {"127.0.0.1", "localhost", "::1"}:
    raise RuntimeError("BACKUP1A_PG_URL tiene que ser un Postgres local")


def _url_de(base: str) -> str:
    return urlsplit(PG_URL)._replace(path="/" + base).geturl()


def _clave() -> str:
    return unquote(urlsplit(PG_URL).password or "")


async def _sql(url: str, *sentencias: str):
    import asyncpg
    conn = await asyncpg.connect(url)
    try:
        ultimo = None
        for s in sentencias:
            ultimo = await conn.fetch(s)
        return ultimo
    finally:
        await conn.close()


def sql(url: str, *sentencias: str):
    return asyncio.run(_sql(url, *sentencias))


def descartables() -> list:
    filas = sql(PG_URL, "SELECT datname FROM pg_database WHERE datname LIKE 'cdi\\_restauracion\\_%'")
    return [f["datname"] for f in filas]


# ── Datos sintéticos de todas las tablas del modelo ─────────────────────────

def _valor(tabla, col, i, hechas):
    from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
    for fk in col.foreign_keys:
        padre = fk.column.table.name
        if padre not in hechas:
            return None  # el ciclo users ↔ organizations: la FK queda vacía
        return hechas[padre][i % len(hechas[padre])][fk.column.name]
    t = col.type
    if isinstance(t, Boolean):
        return i % 2 == 0
    if isinstance(t, Integer):
        return i + 1
    if isinstance(t, Float):
        return i + 1 / 3
    if isinstance(t, DateTime):
        zona = dt.timezone.utc if t.timezone else None
        return dt.datetime(2026, 3, 1 + i, 12, 30, 15, 123456, tzinfo=zona)
    if isinstance(t, JSON):
        return {"i": i, "texto": "ñandú \"x\"", "lista": [1, 2.5, None]}
    if isinstance(t, Text):
        return f"fila {i} de {col.name}: ñandú, tab\t, salto\nde línea, comilla ' y barra \\"
    if isinstance(t, String):
        largo = t.length or 60
        return f"{i}-{tabla.name}.{col.name}"[:largo]
    raise AssertionError(f"tipo sin valor sintético: {tabla.name}.{col.name} {t!r}")


async def _poblar(url: str) -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine
    from proyecto_maria.database.connection import Base
    import proyecto_maria.database.models  # noqa: F401  registra las tablas

    motor = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://", 1))
    hechas = {}
    try:
        async with motor.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            pendientes = list(Base.metadata.tables.values())
            while pendientes:
                lista = [t for t in pendientes if all(
                    fk.column.table.name in hechas or fk.parent.nullable or fk.column.table is t
                    for fk in t.foreign_keys)]
                assert lista, f"no se puede ordenar: {[t.name for t in pendientes]}"
                tabla = lista[0]
                filas = [{c.name: _valor(tabla, c, i, hechas) for c in tabla.columns} for i in range(FILAS)]
                await conn.execute(tabla.insert(), filas)
                hechas[tabla.name] = filas
                pendientes.remove(tabla)
    finally:
        await motor.dispose()
    return hechas


def crear_origen(icu: bool = False) -> str:
    nombre = "b1a_origen_" + secrets.token_hex(6)
    opciones = " LOCALE_PROVIDER icu ICU_LOCALE 'es'" if icu else ""
    sql(PG_URL, f'CREATE DATABASE "{nombre}" TEMPLATE template0{opciones}')
    url = _url_de(nombre)
    asyncio.run(_poblar(url))
    return nombre


@pytest.fixture
def origen():
    nombre = crear_origen()
    yield nombre
    sql(PG_URL, f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')


@pytest.fixture
def origen_icu():
    nombre = crear_origen(icu=True)
    yield nombre
    sql(PG_URL, f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')


def _entorno(origen, env_extra) -> dict:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("COPIA_", "PG")) and k != "BACKUP1A_PG_URL"}
    env["COPIA_PG_BIN"] = PG_BIN
    if origen:
        env["COPIA_ORIGEN_URL"] = _url_de(origen)
    env["COPIA_PRUEBA_URL"] = PG_URL
    env.update(env_extra)
    return env


def correr(*args, origen=None, cwd=None, **env_extra):
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=_entorno(origen, env_extra),
                          capture_output=True, text=True, timeout=300, cwd=cwd, umask=0o022)


def volcar_de_nuevo(origen: str, archivo: Path) -> None:
    """Una copia nueva de la base, sin pasar por el script: la huella que quedó
    es la de antes."""
    archivo.unlink()
    subprocess.run([f"{PG_BIN}/pg_dump", "-Fc", "-f", str(archivo), _url_de(origen)], check=True)


def marca(archivo: Path) -> Path:
    return archivo.with_name(archivo.name + ".sha256")


def huella(archivo: Path) -> dict:
    return json.loads(archivo.with_name(archivo.name + ".huella.json").read_text())


def _copiar_ok(origen, archivo, **env):
    r = correr("copiar", str(archivo), origen=origen, **env)
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def _tablas_usuario(base: str) -> list:
    filas = sql(_url_de(base), "SELECT tablename FROM pg_tables WHERE schemaname NOT IN "
                               "('pg_catalog', 'information_schema')")
    return sorted(f["tablename"] for f in filas)


# ── Copia y restauración ─────────────────────────────────────────────────────

def test_la_copia_de_todas_las_tablas_se_restaura_igual(origen, tmp_path):
    from proyecto_maria.database.connection import Base
    import proyecto_maria.database.models  # noqa: F401

    archivo = tmp_path / "copia.dump"
    r = _copiar_ok(origen, archivo)

    tablas = huella(archivo)["tablas"]
    assert sorted(tablas) == sorted(f"public.{t}" for t in Base.metadata.tables)
    assert {t: v["filas"] for t, v in tablas.items()} == {t: FILAS for t in tablas}
    assert f"copia verificada: {len(tablas)} tablas, {len(tablas) * FILAS} filas" in r.stdout
    assert marca(archivo).read_text().split()[0] == hashlib.sha256(archivo.read_bytes()).hexdigest()
    assert descartables() == []
    assert _tablas_usuario(urlsplit(PG_URL).path.lstrip("/")) == [], "restauró en la base de prueba"


def test_una_fila_cambiada_da_error(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    sql(_url_de(origen), "UPDATE clients SET email = email || 'x' WHERE id = (SELECT min(id) FROM clients)")
    volcar_de_nuevo(origen, archivo)

    r = correr("verificar", str(archivo))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "LA COPIA NO SIRVE" in r.stderr
    assert "public.clients: el contenido no coincide" in r.stderr
    assert "filas" not in r.stderr, "la cantidad de filas es la misma"
    assert not marca(archivo).exists(), "quedó marcada como verificada"
    assert descartables() == []


def test_una_tabla_vacia_da_error(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    sql(_url_de(origen), "DELETE FROM ncm_cache")
    volcar_de_nuevo(origen, archivo)

    r = correr("verificar", str(archivo))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "LA COPIA NO SIRVE" in r.stderr
    assert f"public.ncm_cache: {FILAS} filas al copiar, 0 al restaurar" in r.stderr
    assert not marca(archivo).exists()
    assert descartables() == []


@pytest.mark.parametrize("cambio, dice", [
    ("CREATE TABLE de_mas (x int)", "public.de_mas: no estaba al copiar"),
    ("DROP TABLE ncm_cache", "public.ncm_cache: falta en la restauración"),
])
def test_una_tabla_de_mas_o_de_menos_da_error(origen, tmp_path, cambio, dice):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    sql(_url_de(origen), cambio)
    volcar_de_nuevo(origen, archivo)

    r = correr("verificar", str(archivo))
    assert r.returncode == 1, r.stdout + r.stderr
    assert dice in r.stderr
    assert not marca(archivo).exists()


def test_una_copia_cortada_a_la_mitad_da_error(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    datos = archivo.read_bytes()
    archivo.write_bytes(datos[: len(datos) // 2])

    r = correr("verificar", str(archivo))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "LA COPIA NO SIRVE" in r.stderr
    assert "pg_restore falló" in r.stderr
    assert not marca(archivo).exists()
    assert descartables() == []

    destino = tmp_path / "destino"
    destino.mkdir()
    r = correr("enviar", str(archivo), COPIA_DESTINO=str(destino))
    # Primero el destino: si algo llegó, el rojo lo nombra.
    assert list(destino.iterdir()) == []
    assert r.returncode == 1 and "no está verificada" in r.stderr, r.stdout + r.stderr


@pytest.mark.parametrize("tablas, dice", [
    ([], "la copia está vacía: 0 tablas"),
    (["CREATE TABLE vacia (x int)", "CREATE TABLE otra_vacia (x int)"], "la copia está vacía: 2 tablas, 0 filas"),
])
def test_una_copia_vacia_da_error(tmp_path, tablas, dice):
    """Una dirección equivocada o una base recién creada no dejan una copia
    verificada."""
    nombre = "b1a_vacia_" + secrets.token_hex(6)
    sql(PG_URL, f'CREATE DATABASE "{nombre}" TEMPLATE template0')
    try:
        if tablas:
            sql(_url_de(nombre), *tablas)
        archivo = tmp_path / "copia.dump"
        for orden in ("copiar", "verificar"):
            r = correr(orden, str(archivo), origen=nombre)
            assert r.returncode == 1 and dice in r.stderr, f"{orden}: {r.stdout + r.stderr}"
            assert "copia verificada" not in r.stdout
            assert not marca(archivo).exists()
    finally:
        sql(PG_URL, f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')


def test_otro_esquema_entra_en_la_huella(origen, tmp_path):
    url = _url_de(origen)
    sql(url, "CREATE SCHEMA otro", "CREATE TABLE otro.t (x text)", "INSERT INTO otro.t VALUES ('a')")
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    sql(url, "UPDATE otro.t SET x = 'b'")
    volcar_de_nuevo(origen, archivo)

    r = correr("verificar", str(archivo))
    assert r.returncode == 1 and "otro.t: el contenido no coincide" in r.stderr, r.stdout + r.stderr


# ── Una base que se escribe mientras se copia, y la configuración de cada base ─

def _envoltorio(tmp_path: Path) -> Path:
    """Un pg_dump que anota con qué lo llamaron, hace una escritura en la base
    (como un usuario que guarda mientras se copia) y sigue con el verdadero."""
    carpeta = tmp_path / "bin"
    carpeta.mkdir()
    for nombre in ("pg_dump", "pg_restore"):
        p = carpeta / nombre
        p.write_text(
            "#!/usr/bin/env bash\n"
            f'printf "%s\\0" "$@" >> "{tmp_path}/argv_{nombre}"\n'
            f'printf "%s" "${{PGPASSWORD:-}}" > "{tmp_path}/clave_{nombre}"\n'
            f'if [ "{nombre}" = pg_dump ] && [ -n "${{B1A_ESCRITURA:-}}" ]; then\n'
            f'  "{PG_BIN}/psql" -X -q "$B1A_ESCRITURA_URL" -c "$B1A_ESCRITURA" || exit 9\n'
            "fi\n"
            f'if [ "{nombre}" = pg_restore ] && [ -n "${{B1A_RESTORE:-}}" ]; then\n'
            '  [ "$B1A_RESTORE" = falla ] && exit 1\n'
            f'  echo $$ > "{tmp_path}/pid.tmp" && mv "{tmp_path}/pid.tmp" "{tmp_path}/pid_pg_restore"\n'
            "  exec sleep 30\n"
            "fi\n"
            f'exec "{PG_BIN}/{nombre}" "$@"\n')
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return carpeta


def test_una_escritura_durante_la_copia_no_la_rompe(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo, COPIA_PG_BIN=str(_envoltorio(tmp_path)),
               B1A_ESCRITURA="DELETE FROM ncm_cache WHERE ncm = (SELECT min(ncm) FROM ncm_cache)",
               B1A_ESCRITURA_URL=_url_de(origen))
    assert sql(_url_de(origen), "SELECT count(*) AS n FROM ncm_cache")[0]["n"] == FILAS - 1, \
        "la escritura no pasó"
    assert huella(archivo)["tablas"]["public.ncm_cache"]["filas"] == FILAS


def test_copiar_sale_con_error_si_la_verificacion_falla(origen, tmp_path):
    """El código de salida es lo que mira quien la programa."""
    archivo = tmp_path / "copia.dump"
    r = correr("copiar", str(archivo), origen=origen,
               COPIA_PG_BIN=str(_envoltorio(tmp_path)), B1A_RESTORE="falla")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "pg_restore falló (salida 1)" in r.stderr
    assert not marca(archivo).exists()


def _vivo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return Path(f"/proc/{pid}/stat").read_text().split(")")[-1].split()[0] != "Z"
    except (ProcessLookupError, FileNotFoundError):
        return False


def _sin_restos(pid_restore: Path) -> None:
    assert not _vivo(int(pid_restore.read_text())), "pg_restore quedó corriendo"
    assert descartables() == []


def test_un_corte_no_deja_la_base_ni_el_pg_restore(origen, tmp_path):
    """Con la base descartable creada y pg_restore colgado: el plazo vencido y un
    SIGTERM la borran y matan a pg_restore; un SIGHUP ignorado (nohup) no corta."""
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    pid_restore = tmp_path / "pid_pg_restore"
    env = {"COPIA_PG_BIN": str(_envoltorio(tmp_path)), "B1A_RESTORE": "colgado"}

    r = correr("verificar", str(archivo), COPIA_PLAZO_S="3", **env)
    assert r.returncode == 1 and "no terminó en 3 s" in r.stderr, r.stdout + r.stderr
    assert pid_restore.exists(), "el plazo venció antes de llegar a pg_restore"
    _sin_restos(pid_restore)

    pid_restore.unlink()
    proc = subprocess.Popen([sys.executable, str(SCRIPT), "verificar", str(archivo)],
                            env=_entorno(None, env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            preexec_fn=lambda: signal.signal(signal.SIGHUP, signal.SIG_IGN))
    try:
        limite = time.monotonic() + 60
        while not pid_restore.exists() and proc.poll() is None and time.monotonic() < limite:
            time.sleep(0.1)
        assert pid_restore.exists(), "no llegó a pg_restore"
        proc.send_signal(signal.SIGHUP)
        proc.send_signal(signal.SIGTERM)
        _, err = proc.communicate(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 1 and "se cortó por SIGTERM" in err, err
    _sin_restos(pid_restore)
    assert not marca(archivo).exists()


@pytest.mark.parametrize("plazo", ["0", "-5", "una hora", "²"])
def test_un_plazo_que_no_se_entiende_no_copia(origen, tmp_path, plazo):
    archivo = tmp_path / "copia.dump"
    r = correr("copiar", str(archivo), origen=origen, COPIA_PLAZO_S=plazo)
    assert r.returncode == 1 and "COPIA_PLAZO_S tiene que ser" in r.stderr, r.stdout + r.stderr
    assert list(tmp_path.iterdir()) == []


def test_la_clave_no_va_en_los_argumentos(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo, COPIA_PG_BIN=str(_envoltorio(tmp_path)))
    clave = _clave()
    for nombre in ("pg_dump", "pg_restore"):
        argv = (tmp_path / f"argv_{nombre}").read_text()
        assert clave not in argv and quote(clave, safe="") not in argv, f"la clave va en {nombre}"
        assert (tmp_path / f"clave_{nombre}").read_text() == clave


def test_la_configuracion_de_cada_base_no_cambia_la_huella(origen, tmp_path):
    """Otra zona horaria, otro formato de fecha, de intervalos, de binarios y
    menos decimales en la base copiada que en la de prueba."""
    url = _url_de(origen)
    sql(url, "CREATE TABLE tipos_extra (i interval, b bytea, f double precision, t timestamptz)",
        "INSERT INTO tipos_extra VALUES ('1 day 02:03:04', '\\x00ff', 1/3::float8, '2026-03-01 12:00Z')")
    for ajuste in ("timezone TO 'America/Argentina/Buenos_Aires'", "datestyle TO 'SQL, DMY'",
                   "intervalstyle TO 'sql_standard'", "bytea_output TO 'escape'",
                   "extra_float_digits TO 0"):
        sql(PG_URL, f'ALTER DATABASE "{origen}" SET {ajuste}')

    archivo = tmp_path / "copia.dump"
    r = correr("copiar", str(archivo), origen=origen)
    assert r.returncode == 0, r.stdout + r.stderr


def test_otro_orden_alfabetico_no_cambia_la_huella(origen_icu, tmp_path):
    sql(_url_de(origen_icu), "CREATE TABLE orden (t text)",
        "INSERT INTO orden VALUES ('a'), ('B'), ('ñ'), ('n'), ('Z'), ('o')")
    archivo = tmp_path / "copia.dump"
    r = correr("copiar", str(archivo), origen=origen_icu)
    assert r.returncode == 0, r.stdout + r.stderr


# ── Lo que el script no hace ─────────────────────────────────────────────────

def test_copiar_no_pisa_una_copia_que_ya_existe(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    archivo.write_bytes(b"copia anterior")
    r = correr("copiar", str(archivo), origen=origen)
    assert r.returncode == 1 and "no se pisa una copia" in r.stderr, r.stdout + r.stderr
    assert archivo.read_bytes() == b"copia anterior"


def test_la_direccion_entra_solo_por_variable(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    r = correr("copiar", str(archivo))
    assert r.returncode == 1 and "falta la variable COPIA_ORIGEN_URL" in r.stderr, r.stdout + r.stderr
    assert not archivo.exists()
    r = correr("copiar", str(archivo), origen=origen, COPIA_PRUEBA_URL="")
    assert r.returncode == 1 and "falta la variable COPIA_PRUEBA_URL" in r.stderr, r.stdout + r.stderr
    assert not archivo.exists(), "copió sin saber dónde probarla"

    # Sin la dirección en las variables, tapar() no sabe cuál es la clave: lo
    # que la saca del mensaje de argparse es el reemplazo del argumento.
    clave = _clave()
    for args in (["--base=" + _url_de(origen), str(archivo)], [str(archivo), _url_de(origen)]):
        r = correr("copiar", *args, COPIA_PRUEBA_URL="")
        assert r.returncode == 2, f"acepta la dirección por argumento: {args[0][:6]}"
        assert not archivo.exists()
        assert "unrecognized arguments" in r.stderr, r.stderr
        assert clave not in r.stderr and quote(clave, safe="") not in r.stderr, "el error repite la clave"


def test_los_errores_no_muestran_la_clave(origen, tmp_path):
    clave_mala = "Clave:Mala@" + secrets.token_hex(4)
    partes = urlsplit(_url_de(origen))
    url_mala = partes._replace(
        netloc=f"{partes.username}:{quote(clave_mala, safe='')}@{partes.hostname}:{partes.port}").geturl()
    archivo = tmp_path / "copia.dump"
    for variable in ("COPIA_ORIGEN_URL", "COPIA_PRUEBA_URL"):
        env = {"COPIA_ORIGEN_URL": _url_de(origen), variable: url_mala}
        r = correr("copiar", str(archivo), **env)
        assert r.returncode == 1, r.stdout + r.stderr
        salida = r.stdout + r.stderr
        assert clave_mala not in salida and quote(clave_mala, safe="") not in salida
        assert "Mala" not in salida
        if archivo.exists():
            archivo.unlink()
        for extra in (".huella.json", ".sha256"):
            p = archivo.with_name(archivo.name + extra)
            if p.exists():
                p.unlink()


# ── Envío al destino de prueba ───────────────────────────────────────────────

def test_enviar_lleva_la_copia_verificada_al_destino(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    destino = tmp_path / "destino"
    destino.mkdir()

    r = correr("enviar", str(archivo), COPIA_DESTINO=str(destino))
    assert r.returncode == 0, r.stdout + r.stderr
    assert sorted(p.name for p in destino.iterdir()) == \
        ["copia.dump", "copia.dump.huella.json", "copia.dump.sha256"]
    assert (destino / "copia.dump").read_bytes() == archivo.read_bytes()
    # La copia es la base entera: sólo la lee quien la sacó, acá y en el destino.
    for p in [*tmp_path.glob("copia.dump*"), *destino.iterdir()]:
        assert stat.S_IMODE(p.stat().st_mode) == 0o600, f"{p.name}: {oct(p.stat().st_mode)}"

    r = correr("enviar", str(archivo), COPIA_DESTINO=str(destino))
    assert r.returncode == 1 and "ya existe en el destino" in r.stderr, r.stdout + r.stderr


def test_enviar_no_lleva_una_copia_que_cambio(origen, tmp_path):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    with archivo.open("ab") as f:
        f.write(b"\0")
    destino = tmp_path / "destino"
    destino.mkdir()

    r = correr("enviar", str(archivo), COPIA_DESTINO=str(destino))
    assert r.returncode == 1 and "cambió desde que se verificó" in r.stderr, r.stdout + r.stderr
    assert list(destino.iterdir()) == []


@pytest.mark.parametrize("destino, dice", [
    ("s3://cubo/copias", "COPIA_DESTINO: enviar a un servicio no está soportado"),
    ("relativo/copias", "COPIA_DESTINO tiene que ser una carpeta local"),
    ("{tmp}/no_existe", "COPIA_DESTINO tiene que ser una carpeta local"),
    ("", "falta la variable COPIA_DESTINO"),
])
def test_enviar_solo_a_una_carpeta_local(origen, tmp_path, destino, dice):
    archivo = tmp_path / "copia.dump"
    _copiar_ok(origen, archivo)
    # La carpeta relativa existe desde donde se corre: lo que la rechaza es
    # que no sea la ruta entera.
    (tmp_path / "relativo" / "copias").mkdir(parents=True)
    r = correr("enviar", str(archivo), COPIA_DESTINO=destino.replace("{tmp}", str(tmp_path)), cwd=tmp_path)
    assert r.returncode == 1 and dice in r.stderr, r.stdout + r.stderr
    assert sorted(p.name for p in (tmp_path / "relativo" / "copias").iterdir()) == []
