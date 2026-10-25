"""CLIENTE-1b: los clientes con una fecha de inicio de actividad que no sirve.

Antes del arreglo, el alta y la edición guardaban lo que llegaba cortado a
diez caracteres: un `null` quedaba «None» y un año de cinco cifras, cortado.
Este script informa cuántos clientes quedaron así y cuáles (sólo el id, sin
otros datos del cliente). «No sirve» es lo que el TXT no acepta: el mismo
criterio que `fecha_inicio_actividad` del generador.

Por defecto sólo lee. Con `--arreglar-none` deja vacías las que dicen «None»
(eran un `null`); las otras no se tocan: no se sabe qué fecha quisieron poner.

    python scripts/datos/clientes_fecha_inic_activ.py --base sqlite+aiosqlite:///./prueba.db
    python scripts/datos/clientes_fecha_inic_activ.py --base postgresql://... --arreglar-none

Correrlo en producción lo decide Emi.
"""
import argparse
import asyncio
import os
import re
import sys
from urllib.parse import parse_qsl, quote, quote_plus, unquote, unquote_plus, urlsplit

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from proyecto_maria.core.maria_generator import fecha_inicio_actividad  # noqa: E402


def _url_async(url: str) -> str:
    # Como `database/connection.py`: Railway da postgres:// o postgresql://.
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+asyncpg://" + url[len(prefijo):]
    if url.startswith("sqlite://"):
        return "sqlite+aiosqlite://" + url[len("sqlite://"):]
    return url


def _donde_y_secretos(base: str):
    """Dónde está la base (host, puerto y base, sin usuario ni consulta) y lo
    que puede ser la clave: todo lo de antes del último «@» y los valores de la
    consulta. Se lee del texto escrito, no de SQLAlchemy: una clave con «@» o
    «;» sin escapar, o en `?password=`, SQLAlchemy no la ve como clave."""
    partes = urlsplit(base)
    usuario, _, lugar = partes.netloc.rpartition("@")
    secretos = {usuario, *re.split(r"[:;@]", usuario)}
    secretos |= {v for _, v in parse_qsl(partes.query, keep_blank_values=True)}
    try:
        host = partes.hostname or ""
    except ValueError:
        host = ""
    return lugar + partes.path, host, {s for s in secretos if s}


def _sin_clave(texto: str, secretos, host: str = "") -> str:
    """El texto de un error sin ninguno de los secretos, como vengan o
    escapados. El host no se tapa: una clave «1» no borra «127.0.0.1»."""
    formas = set()
    for s in secretos:
        for crudo in {s, unquote(s), unquote_plus(s)}:
            formas |= {crudo, quote(crudo, safe=""), quote_plus(crudo)}
    if host:
        texto = texto.replace(host, "\0")
    for forma in sorted(formas - {""}, key=len, reverse=True):
        texto = texto.replace(forma, "***")
    return texto.replace("\0", host) if host else texto


def clasificar(filas):
    """De (id, fecha) a las filas (id, fecha) con «None» y los ids con otra
    fecha que no sirve."""
    con_none, no_sirven = [], []
    for cid, fecha in filas:
        texto = (fecha or "").strip()
        if not texto:
            continue
        if texto == "None":
            con_none.append((cid, fecha))
            continue
        try:
            fecha_inicio_actividad(texto)
        except ValueError:
            no_sirven.append(cid)
    return sorted(con_none), sorted(no_sirven)


async def revisar(url: str, arreglar_none: bool) -> dict:
    engine = create_async_engine(_url_async(url))
    try:
        async with engine.begin() as conn:
            filas = (await conn.execute(text(
                "SELECT id, fecha_inic_activ FROM clients WHERE fecha_inic_activ IS NOT NULL"
            ))).all()
            con_none, no_sirven = clasificar(filas)
            arreglados = 0
            if arreglar_none:
                # Las informadas, por id, y sólo si siguen con lo que se leyó.
                for cid, fecha in con_none:
                    resultado = await conn.execute(text(
                        "UPDATE clients SET fecha_inic_activ = '' "
                        "WHERE id = :id AND fecha_inic_activ = :fecha"
                    ), {"id": cid, "fecha": fecha})
                    arreglados += resultado.rowcount
    finally:
        await engine.dispose()
    return {"con_none": [cid for cid, _ in con_none], "no_sirven": no_sirven,
            "arreglados": arreglados}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--base", required=True, help="URL de la base (no se toma de DATABASE_URL)")
    p.add_argument("--arreglar-none", action="store_true",
                   help="deja vacías las fechas que dicen «None»; sin esto sólo se lee")
    args = p.parse_args(argv)
    # SQLite crea el archivo que no existe: una ruta mal escrita dejaría una
    # base vacía y un traceback.
    # Un error de Python mostraría la URL entera, con la clave (CLIENTE-1c).
    try:
        url = make_url(_url_async(args.base))  # también rechaza el puerto «:abc»
    except (ArgumentError, ValueError):
        p.error("--base no es una URL de base que se entienda "
                "(por ejemplo postgresql://usuario:clave@host/base)")
    if (url.get_backend_name() == "sqlite" and url.database not in (None, "", ":memory:")
            and not os.path.exists(url.database)):
        p.error(f"la base sqlite no existe: {url.database}")
    try:
        r = asyncio.run(revisar(args.base, args.arreglar_none))
    except Exception as e:  # noqa: BLE001 - se informa sin traceback
        donde, host, secretos = _donde_y_secretos(args.base)
        if url.get_backend_name() == "sqlite":
            donde = url.database or donde
        if url.password:
            secretos.add(url.password)
        print(f"No se pudo revisar la base {donde}: "
              + _sin_clave(f"{type(e).__name__}: {e}", secretos, host), file=sys.stderr)
        return 2
    print(f"Con «None»: {len(r['con_none'])}")
    for cid in r["con_none"]:
        print(f"  {cid}")
    print(f"Con una fecha que no sirve: {len(r['no_sirven'])}")
    for cid in r["no_sirven"]:
        print(f"  {cid}")
    if args.arreglar_none:
        print(f"Quedaron vacías: {r['arreglados']}")
    else:
        print("No se cambió nada (para dejar vacías las «None»: --arreglar-none).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
