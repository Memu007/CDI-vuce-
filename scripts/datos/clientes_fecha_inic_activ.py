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
import unicodedata
from urllib.parse import quote, quote_plus, unquote, unquote_plus

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


# Lo que parte la URL escrita en pedazos que pueden ser la clave o el usuario.
_SEPARADORES = r"[:;@/?#]"


def _secretos(base: str, url) -> set:
    """Lo que puede ser la clave: lo que SQLAlchemy leyó como clave, usuario y
    valores de la consulta, y además todo lo de antes del último «@» del texto
    escrito, entero y partido en «:», «;», «@», «/», «?» y «#». Una clave mal
    escapada SQLAlchemy la puede leer como host o base: también se tapa. El
    usuario se tapa como la clave."""
    crudo = base.split("://", 1)[-1]
    antes = crudo.rpartition("@")[0]
    secretos = {antes, antes.partition(":")[2], *re.split(_SEPARADORES, antes),
                url.password or "", url.username or ""}
    for valor in url.query.values():
        secretos |= set(valor) if isinstance(valor, tuple) else {valor}
    return {s for s in secretos if s}


def _tapar(texto: str, secretos, visibles=()) -> str:
    """El texto sin ninguno de los secretos, como vengan o escapados. Se tapa
    sólo el secreto entero, no un pedazo de palabra: un usuario «u» no rompe
    «ConnectionRefusedError». Los `visibles` (los pedazos del host que no son
    secretos) quedan: una clave «1» no borra «127.0.0.1»; una clave que los
    contiene se tapa igual, porque se prueba primero lo más largo."""
    formas = set()
    for s in secretos:
        for crudo in {s, unquote(s), unquote_plus(s), unicodedata.normalize("NFKC", s)}:
            formas |= {crudo, quote(crudo, safe=""), quote_plus(crudo)}
    formas.discard("")
    visibles = {v for v in visibles if v} - formas
    if not formas:
        return texto
    opciones = []
    for f in sorted(formas | visibles, key=len, reverse=True):
        patron = re.escape(f)
        if f not in visibles:
            if re.match(r"\w", f):
                patron = r"(?<!\w)" + patron
            if re.search(r"\w\Z", f):
                patron += r"(?!\w)"
        opciones.append(patron)
    return re.sub("|".join(opciones),
                  lambda m: m.group(0) if m.group(0) in visibles else "***", texto)


def _donde(url, secretos) -> str:
    """Host, puerto y base de lo que se conectó, con los pedazos que son
    secretos tapados."""
    if url.get_backend_name() == "sqlite":
        lugar = url.database or ""
    else:
        lugar = (url.host or "") + (f":{url.port}" if url.port else "") + (
            f"/{url.database}" if url.database else "")
    pedazos = re.split(f"({_SEPARADORES})", lugar)
    return "".join("***" if p in secretos else p for p in pedazos)


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


async def revisar(url, arreglar_none: bool) -> dict:
    # `url` es la de `make_url`: lo que conecta es lo mismo que se tapa.
    engine = create_async_engine(url)
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
        r = asyncio.run(revisar(url, args.arreglar_none))
    except Exception as e:  # noqa: BLE001 - se informa sin traceback
        try:
            secretos = _secretos(args.base, url)
            visibles = set(re.split(_SEPARADORES, url.host or "")) - secretos
            donde = _tapar(_donde(url, secretos), secretos, visibles)
            detalle = _tapar(f"{type(e).__name__}: {e}", secretos, visibles)
        except Exception:  # noqa: BLE001 - tapar nunca muestra un traceback
            donde, detalle = "(sin detalle)", type(e).__name__
        print(f"No se pudo revisar la base {donde}: {detalle}", file=sys.stderr)
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
