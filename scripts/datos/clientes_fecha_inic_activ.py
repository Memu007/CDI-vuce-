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
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from proyecto_maria.core.maria_generator import fecha_inicio_actividad  # noqa: E402


def _url_async(url: str) -> str:
    # Como `database/connection.py`: Railway da postgres:// o postgresql://.
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+asyncpg://" + url[len(prefijo):]
    return url


def clasificar(filas):
    """De (id, fecha) a los ids con «None» y los ids con otra fecha que no sirve."""
    con_none, no_sirven = [], []
    for cid, fecha in filas:
        texto = (fecha or "").strip()
        if not texto:
            continue
        if texto == "None":
            con_none.append(cid)
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
            if arreglar_none and con_none:
                # Sólo las que siguen diciendo «None» al momento de escribir.
                resultado = await conn.execute(text(
                    "UPDATE clients SET fecha_inic_activ = '' WHERE TRIM(fecha_inic_activ) = 'None'"
                ))
                arreglados = resultado.rowcount
    finally:
        await engine.dispose()
    return {"con_none": con_none, "no_sirven": no_sirven, "arreglados": arreglados}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--base", required=True, help="URL de la base (no se toma de DATABASE_URL)")
    p.add_argument("--arreglar-none", action="store_true",
                   help="deja vacías las fechas que dicen «None»; sin esto sólo se lee")
    args = p.parse_args(argv)
    r = asyncio.run(revisar(args.base, args.arreglar_none))
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
