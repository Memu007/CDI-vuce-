"""BACKUP-1a: copia de la base Postgres, restaurada y comparada antes de darla por buena.

Tres pasos, cada uno con su orden:

    copiar <archivo>     pg_dump -Fc de COPIA_ORIGEN_URL, con la huella de cada
                         tabla sacada en el mismo instante; después, verificar.
    verificar <archivo>  restaura la copia en una base descartable del servidor
                         de COPIA_PRUEBA_URL, la compara con la huella y la borra.
                         Si coincide deja <archivo>.sha256; si no, sale con 1.
    enviar <archivo>     lleva una copia verificada a COPIA_DESTINO (por ahora,
                         sólo una carpeta local: el destino real lo define Emi).

La huella de una tabla es la cantidad de filas y un sha256 de sus filas como
texto, ordenadas byte a byte. Se calcula con la misma configuración de sesión
de los dos lados: la zona horaria o el formato de fecha de cada base no la
cambian.

Las direcciones entran sólo por variable (un argumento queda en el historial
del shell). La clave no se pasa a pg_dump ni a pg_restore en los argumentos
sino en PGPASSWORD, y ningún error la muestra.

    COPIA_ORIGEN_URL=... COPIA_PRUEBA_URL=... python scripts/datos/copia_base.py copiar /copias/cdi.dump
    COPIA_DESTINO=/mnt/copias python scripts/datos/copia_base.py enviar /copias/cdi.dump

COPIA_PG_BIN es la carpeta de pg_dump y pg_restore (por defecto, los del PATH).
COPIA_PLAZO_S es cuántos segundos puede durar la orden entera (por defecto, 3600):
en copiar, cuenta también la verificación.
Correrlo contra producción lo decide Emi.
"""
import argparse
import asyncio
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import sys
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.datos.clientes_fecha_inic_activ import _SEPARADORES, _tapar  # noqa: E402

FORMATO = "cdi-copia-1"
ESQUEMAS = ("postgres://", "postgresql://", "postgresql+asyncpg://")
VARIABLES = ("COPIA_ORIGEN_URL", "COPIA_PRUEBA_URL")
TOPE_BORRADO_S = 60

# La salida de un valor como texto depende de la sesión: se fija igual al
# copiar y al restaurar, así la configuración de cada base no cambia la huella.
SESION = (
    "SET TimeZone TO 'UTC'",
    "SET DateStyle TO 'ISO, YMD'",
    "SET IntervalStyle TO 'postgres'",
    "SET extra_float_digits TO 3",
    "SET bytea_output TO 'hex'",
)

TABLAS = r"""
    SELECT tabla FROM (
        SELECT format('%I.%I', n.nspname, c.relname) AS tabla
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind = 'r'
          AND n.nspname NOT IN ('pg_catalog', 'information_schema')
          AND n.nspname NOT LIKE 'pg\_toast%' AND n.nspname NOT LIKE 'pg\_temp\_%'
    ) AS s
    ORDER BY tabla COLLATE "C"
"""


class Falla(Exception):
    """Un error para quien corre el script. Se muestra tapado igual."""


# ── Direcciones ──────────────────────────────────────────────────────────────

class Direccion:
    """Una dirección leída de su variable: la URL sin la clave y la clave."""

    def __init__(self, variable: str):
        crudo = os.environ.get(variable, "")
        if not crudo:
            raise Falla(f"falta la variable {variable}")
        resto = next((crudo[len(e):] for e in ESQUEMAS if crudo.startswith(e)), None)
        if resto is None:
            raise Falla(f"{variable} no es una dirección postgresql://")
        partes = urlsplit("postgresql://" + resto)
        datos, _, servidor = partes.netloc.rpartition("@")
        usuario, con_clave, clave = datos.partition(":")
        self.clave = unquote(clave) if con_clave else None
        consulta = []
        for k, v in parse_qsl(partes.query, keep_blank_values=True):
            if k == "password":
                self.clave = v
            else:
                consulta.append((k, v))
        try:
            partes.port
        except ValueError:
            raise Falla(f"{variable}: el puerto no es un número") from None
        self.servidor = servidor
        self.usuario = usuario
        self.ruta = partes.path
        self.consulta = urlencode(consulta)

    def url(self, base: str = None) -> str:
        """La URL sin clave; con `base`, la de otra base del mismo servidor."""
        ruta = "/" + quote(base, safe="") if base is not None else self.ruta
        lugar = f"{self.usuario}@{self.servidor}" if self.usuario else self.servidor
        return urlunsplit(("postgresql", lugar, ruta, self.consulta, ""))

    def entorno(self) -> dict:
        env = dict(os.environ)
        if self.clave is not None:
            env["PGPASSWORD"] = self.clave
        return env

    async def conectar(self, base: str = None):
        import asyncpg
        conn = await asyncpg.connect(dsn=self.url(base), password=self.clave)
        for sentencia in SESION:
            await conn.execute(sentencia)
        return conn


def tapar(texto: str) -> str:
    """El texto sin nada que pueda ser una clave de las dos direcciones: todo
    lo de antes del último «@», entero y en pedazos, y el `password=` de la
    consulta. Lo que es host queda a la vista."""
    secretos, visibles = set(), set()
    for variable in VARIABLES:
        crudo = os.environ.get(variable, "")
        resto = crudo.split("://", 1)[-1]
        antes, _, despues = resto.rpartition("@")
        clave = antes.partition(":")[2]
        secretos |= {antes, clave, unquote(clave), *re.split(_SEPARADORES, antes)}
        for k, v in parse_qsl(urlsplit("x://" + resto).query, keep_blank_values=True):
            if k == "password":
                secretos |= {v, quote(v, safe="")}
        visibles |= set(re.split(_SEPARADORES, despues.split("/", 1)[0]))
    secretos.discard("")
    return _tapar(texto, secretos, visibles - secretos)


def _bin(nombre: str) -> str:
    carpeta = os.environ.get("COPIA_PG_BIN")
    return os.path.join(carpeta, nombre) if carpeta else nombre


# ── Huella ───────────────────────────────────────────────────────────────────

@contextlib.asynccontextmanager
async def _instante(conn):
    """Una transacción de sólo lectura que ve la base en un único instante. Si
    algo falla en medio de un COPY, el ROLLBACK queda esperando: se corta la
    conexión, y con ella la transacción."""
    tx = conn.transaction(isolation="repeatable_read", readonly=True)
    await tx.start()
    try:
        yield
    except BaseException:
        conn.terminate()
        raise
    await tx.commit()


async def huella(conn) -> dict:
    """Por tabla, {"filas", "sha256"} de sus filas como texto, en orden de bytes
    (COLLATE "C": el orden alfabético de la base no cuenta). COPY escapa los
    saltos de línea de los valores: cada «\\n» es una fila."""
    tablas = {}
    for registro in await conn.fetch(TABLAS):
        tabla = registro["tabla"]
        suma, filas = hashlib.sha256(), 0

        async def sumar(datos, suma=suma):
            nonlocal filas
            suma.update(datos)
            filas += datos.count(b"\n")

        await conn.copy_from_query(
            f'SELECT fila FROM (SELECT ROW(t.*)::text COLLATE "C" AS fila FROM {tabla} AS t) AS s '
            "ORDER BY fila", output=sumar)
        tablas[tabla] = {"filas": filas, "sha256": suma.hexdigest()}
    return tablas


def diferencias(antes: dict, despues: dict) -> list:
    """Lo que no coincide entre la huella de la copia y la de la restauración."""
    salida = []
    for tabla in sorted(antes.keys() | despues.keys()):
        a, d = antes.get(tabla), despues.get(tabla)
        if d is None:
            salida.append(f"{tabla}: falta en la restauración")
        elif a is None:
            salida.append(f"{tabla}: no estaba al copiar")
        elif a["filas"] != d["filas"]:
            salida.append(f"{tabla}: {a['filas']} filas al copiar, {d['filas']} al restaurar")
        elif a["sha256"] != d["sha256"]:
            salida.append(f"{tabla}: el contenido no coincide")
    return salida


# ── Archivos ─────────────────────────────────────────────────────────────────

def _de_huella(archivo: str) -> str:
    return archivo + ".huella.json"


def _de_marca(archivo: str) -> str:
    return archivo + ".sha256"


def sha256_de(ruta: str) -> str:
    suma = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            suma.update(bloque)
    return suma.hexdigest()


def _temporal(ruta: str) -> str:
    return f"{ruta}.parcial-{secrets.token_hex(4)}"


def _fijar(temporal: str, ruta: str) -> None:
    """Deja el temporal con su nombre sin pisar nada: el enlace falla si ya hay
    un archivo con ese nombre."""
    try:
        os.link(temporal, ruta)
    except FileExistsError:
        raise Falla(f"ya existe {ruta}") from None
    finally:
        os.unlink(temporal)


def _escribir(ruta: str, texto: str) -> None:
    temporal = _temporal(ruta)
    with open(temporal, "w", encoding="utf-8") as f:
        f.write(texto)
    _fijar(temporal, ruta)


def leer_huella(archivo: str) -> dict:
    try:
        with open(_de_huella(archivo), encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        raise Falla(f"falta la huella {_de_huella(archivo)}") from None
    except ValueError:
        raise Falla(f"la huella {_de_huella(archivo)} no se entiende") from None
    tablas = datos.get("tablas") if isinstance(datos, dict) else None
    if (not isinstance(tablas, dict) or datos.get("formato") != FORMATO or not all(
            isinstance(v, dict) and isinstance(v.get("filas"), int) and isinstance(v.get("sha256"), str)
            for v in tablas.values())):
        raise Falla(f"la huella {_de_huella(archivo)} no se entiende")
    return datos


async def _esperar(proc) -> str:
    """El stderr del hijo. Si se corta la espera, el hijo no queda corriendo."""
    try:
        _, err = await proc.communicate()
    except BaseException:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
        raise
    return err.decode("utf-8", "replace")


async def _correr(*args, env) -> tuple:
    proc = await asyncio.create_subprocess_exec(
        *args, stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE, env=env)
    err = await _esperar(proc)
    return proc.returncode, err


def _filas(tablas: dict) -> int:
    """Una dirección equivocada o una base recién creada restauran «igual»."""
    filas = sum(t["filas"] for t in tablas.values())
    if not filas:
        raise Falla(f"la copia está vacía: {len(tablas)} tablas, 0 filas")
    return filas


async def _borrar_restauracion(admin, base: str) -> None:
    """Un corte no deja el borrado a medias: se termina, con su propio tope para
    que un DROP colgado no espere para siempre, y después sigue el corte."""
    async def borrar():
        try:
            await admin.execute(f'DROP DATABASE IF EXISTS "{base}" WITH (FORCE)')
            await admin.close()
        finally:
            if not admin.is_closed():
                admin.terminate()
    tarea = asyncio.ensure_future(asyncio.wait_for(borrar(), TOPE_BORRADO_S))
    try:
        await asyncio.shield(tarea)
    except asyncio.CancelledError:
        await asyncio.gather(tarea, return_exceptions=True)
        raise
    except TimeoutError:
        raise Falla(f"no se pudo borrar {base} en {TOPE_BORRADO_S} s: hay que borrarla a mano") from None


def _resumen(err: str) -> str:
    lineas = [linea[:200] for linea in err.strip().splitlines()[:5]]
    return tapar("\n    ".join(lineas))


# ── Órdenes ──────────────────────────────────────────────────────────────────

async def copiar(archivo: str) -> int:
    for ruta in (archivo, _de_huella(archivo), _de_marca(archivo)):
        if os.path.lexists(ruta):
            raise Falla(f"ya existe {ruta}: no se pisa una copia")
    origen = Direccion("COPIA_ORIGEN_URL")
    Direccion("COPIA_PRUEBA_URL")  # que falte se sabe antes de copiar
    temporal = _temporal(archivo)
    listo = False
    conn = await origen.conectar()
    try:
        # pg_dump toma la base en el mismo instante que la huella: lo que se
        # escriba mientras copia no queda en ninguna de las dos.
        async with _instante(conn):
            instante = await conn.fetchval("SELECT pg_export_snapshot()")
            proc = await asyncio.create_subprocess_exec(
                _bin("pg_dump"), "-Fc", "--no-password", f"--snapshot={instante}",
                f"--file={temporal}", f"--dbname={origen.url()}",
                stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE, env=origen.entorno())
            volcado = asyncio.ensure_future(_esperar(proc))
            try:
                tablas = await huella(conn)
            except BaseException:
                # Cancelar la espera no alcanza: si todavía no arrancó, no mata a pg_dump.
                if proc.returncode is None:
                    proc.kill()
                await asyncio.gather(volcado, return_exceptions=True)
                raise
            err = await volcado
            if proc.returncode != 0:
                raise Falla(f"pg_dump falló (salida {proc.returncode}):\n    {_resumen(err)}")
            _filas(tablas)
            datos = {
                "formato": FORMATO,
                "creada": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "servidor": await conn.fetchval("SHOW server_version"),
                "codificacion": await conn.fetchval("SELECT pg_encoding_to_char(encoding) "
                                                    "FROM pg_database WHERE datname = current_database()"),
                "tablas": tablas,
            }
        _fijar(temporal, archivo)
        listo = True
    finally:
        await conn.close()
        if not listo and os.path.lexists(temporal):
            os.unlink(temporal)
    _escribir(_de_huella(archivo), json.dumps(datos, indent=1, sort_keys=True) + "\n")
    print(f"copia: {archivo}")
    return await verificar(archivo)


async def verificar(archivo: str) -> int:
    # Hasta que esta corrida no dé igual, la copia no está verificada.
    if os.path.lexists(_de_marca(archivo)):
        os.unlink(_de_marca(archivo))
    if not os.path.isfile(archivo):
        raise Falla(f"no existe la copia {archivo}")
    datos = leer_huella(archivo)
    if not re.fullmatch(r"[A-Z0-9_]+", str(datos.get("codificacion", ""))):
        raise Falla(f"la huella {_de_huella(archivo)} no se entiende")
    filas = _filas(datos["tablas"])
    prueba = Direccion("COPIA_PRUEBA_URL")
    suma = sha256_de(archivo)
    base = "cdi_restauracion_" + secrets.token_hex(8)
    admin = await prueba.conectar()
    try:
        await admin.execute(f'CREATE DATABASE "{base}" TEMPLATE template0 '
                            f"ENCODING '{datos['codificacion']}' LOCALE 'C'")
        codigo, err = await _correr(
            _bin("pg_restore"), "--exit-on-error", "--single-transaction", "--no-owner",
            "--no-acl", "--no-password", f"--dbname={prueba.url(base)}", archivo,
            env=prueba.entorno())
        if codigo != 0:
            problemas = [f"pg_restore falló (salida {codigo}):\n    {_resumen(err)}"]
        else:
            restaurada = await prueba.conectar(base)
            try:
                async with _instante(restaurada):
                    problemas = diferencias(datos["tablas"], await huella(restaurada))
            finally:
                await restaurada.close()
    finally:
        await _borrar_restauracion(admin, base)
    if problemas:
        print("LA COPIA NO SIRVE:\n  " + "\n  ".join(problemas), file=sys.stderr)
        return 1
    _escribir(_de_marca(archivo), f"{suma}  {os.path.basename(archivo)}\n")
    print(f"copia verificada: {len(datos['tablas'])} tablas, {filas} filas")
    return 0


async def enviar(archivo: str) -> int:
    destino = os.environ.get("COPIA_DESTINO", "")
    if not destino:
        raise Falla("falta la variable COPIA_DESTINO")
    if "://" in destino:
        raise Falla("COPIA_DESTINO: enviar a un servicio no está soportado todavía (lo define Emi)")
    if not os.path.isabs(destino) or not os.path.isdir(destino):
        raise Falla("COPIA_DESTINO tiene que ser una carpeta local que exista, con la ruta entera")
    try:
        with open(_de_marca(archivo), encoding="utf-8") as f:
            verificada = f.read().split()[0]
    except (FileNotFoundError, IndexError):
        raise Falla(f"la copia {archivo} no está verificada: correr verificar") from None
    if sha256_de(archivo) != verificada:
        raise Falla(f"la copia {archivo} cambió desde que se verificó")
    leer_huella(archivo)
    # La marca va última: en el destino, una copia sin su .sha256 está a medias.
    origenes = [archivo, _de_huella(archivo), _de_marca(archivo)]
    finales = [os.path.join(destino, os.path.basename(r)) for r in origenes]
    for final in finales:
        if os.path.lexists(final):
            raise Falla(f"ya existe en el destino: {final}")
    for origen, final in zip(origenes, finales):
        temporal = _temporal(final)
        shutil.copyfile(origen, temporal)
        if origen == archivo and sha256_de(temporal) != verificada:
            os.unlink(temporal)
            raise Falla(f"la copia llegó distinta a {destino}")
        _fijar(temporal, final)
    print(f"enviada a {destino}: {os.path.basename(archivo)}")
    return 0


ORDENES = {"copiar": copiar, "verificar": verificar, "enviar": enviar}


async def _cortable(orden, archivo: str) -> int:
    """La orden, cortada por el plazo o una señal como si fallara, así sus `finally`
    limpian; sólo cuenta el primer corte, para que otro no interrumpa la limpieza."""
    plazo = os.environ.get("COPIA_PLAZO_S", "3600")
    if not re.fullmatch(r"[0-9]+", plazo) or int(plazo) == 0:
        raise Falla("COPIA_PLAZO_S tiene que ser una cantidad entera de segundos mayor que 0")
    tarea, loop, motivo = asyncio.current_task(), asyncio.get_running_loop(), []

    def cortar(por: str) -> None:
        if not motivo:
            motivo.append(por)
            tarea.cancel()

    for senal in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        # Quien la ignoró a propósito (nohup) no quiere que corte.
        if signal.getsignal(senal) is not signal.SIG_IGN:
            loop.add_signal_handler(senal, cortar, f"se cortó por {senal.name} antes de terminar")
    loop.call_later(int(plazo), cortar, f"no terminó en {plazo} s")
    try:
        return await orden(archivo)
    except asyncio.CancelledError:
        if not motivo:
            raise
        raise Falla(motivo[0]) from None


class _Argumentos(argparse.ArgumentParser):
    def error(self, message):
        # Un argumento que no se entiende sale en el mensaje: si alguien pasó
        # la dirección, no se repite.
        for arg in sys.argv[1:]:
            if "://" in arg or "@" in arg:
                message = message.replace(arg, "***")
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {tapar(message)}\n"
                     "(las direcciones van en COPIA_ORIGEN_URL y COPIA_PRUEBA_URL, nunca como argumento)\n")


def main(argv=None) -> int:
    p = _Argumentos(description=__doc__.split("\n\n")[0])
    ordenes = p.add_subparsers(dest="orden", required=True, parser_class=_Argumentos)
    for nombre, ayuda in (("copiar", "saca la copia y la verifica"),
                          ("verificar", "restaura la copia y la compara con su huella"),
                          ("enviar", "lleva una copia verificada a COPIA_DESTINO")):
        ordenes.add_parser(nombre, help=ayuda).add_argument("archivo")
    args = p.parse_args(argv)
    # La copia es la base entera: lo que escriben el script y pg_dump lo lee
    # sólo quien lo corre.
    os.umask(0o077)
    try:
        orden, archivo = ORDENES[args.orden], os.path.abspath(args.archivo)
        # enviar sólo copia archivos: no tiene hijos ni bases que limpiar al cortarse.
        return asyncio.run(orden(archivo) if orden is enviar else _cortable(orden, archivo))
    except Falla as e:
        print(f"error: {tapar(str(e))}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001 - se informa sin traceback: puede tener la dirección
        try:
            detalle = tapar(f"{type(e).__name__}: {e}")
        except Exception:  # noqa: BLE001 - tapar nunca muestra un traceback
            detalle = type(e).__name__
        print(f"error: {detalle}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
