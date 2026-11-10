"""Qué letras pasan a minúscula distinto en Python y en Postgres.

El tope de recuperar cuenta por la cuenta encontrada con lower() de la base;
el email nuevo se valida en Python. Una letra que difiera es una variante del
mismo email que la base encuentra y Python no. Recorre lo imprimible hasta
U+2FFFF con la collation de la base, ICU y ucs_basic.

uso: python scripts/testing/email1_minusculas_pg.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import asyncio, sys, asyncpg
async def main(url):
    c = await asyncpg.connect(url)
    chars = [chr(i) for i in range(0x20, 0x30000) if not 0xD800 <= i <= 0xDFFF and chr(i).isprintable()]
    print("PG", (await c.fetchval("show server_version")), "collation base:", await c.fetchval("select datcollate from pg_database where datname=current_database()"))
    for coll in ("default", "und-x-icu", "ucs_basic"):
        q = "select lower(x) from unnest($1::text[]) with ordinality t(x,n) order by n" if coll == "default" else f'select lower(x collate "{coll}") from unnest($1::text[]) with ordinality t(x,n) order by n'
        pg = [r[0] for r in await c.fetch(q, chars)]
        dif = [ch for ch, p in zip(chars, pg) if ch.lower() != p]
        print(f"{coll}: {len(dif)} letras con minúscula distinta en Python; primeras: {[f'U+{ord(d):04X}' for d in dif[:5]]}")
    await c.close()
asyncio.run(main(sys.argv[1]))
