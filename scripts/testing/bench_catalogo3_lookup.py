"""Mide lo que hace /api/catalog/lookup: match_items + lookup_client_memory por ítem.

Desde la raíz de un worktree, con su venv y las variables de las pruebas:
  python scripts/testing/bench_catalogo3_lookup.py 65      # o 430; KANA=1 o ACENTOS=1 cambian las palabras
Imprime «largo=… proveedor=…s cliente=…s total=…s»: correrlo igual en la base y comparar el total.
"""
import asyncio, os, sys, tempfile, time, random
fd, path = tempfile.mkstemp(suffix=".db", dir=os.environ.get("BENCH_DIR")); os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{path}"
sys.path.insert(0, os.getcwd())
from proyecto_maria.database.connection import init_db, AsyncSessionLocal
from proyecto_maria.core import catalog_service as cs
from proyecto_maria.services.client_memory import upsert_client_product_history, lookup_client_memory

LARGO = int(sys.argv[1])
rnd = random.Random(7)
PAL = (["tornillo", "tuerca", "arandela", "acero", "inox", "cable", "cobre", "bulón", "perno", "zincado", "hexágonal", "allen", "rosca", "fina", "gruesa", "plástico", "goma", "válvula"] if os.environ.get("ACENTOS") else None) or ["tornillo", "tuerca", "arandela", "acero", "inox", "cable", "cobre", "bulon", "perno",
       "zincado", "hexagonal", "allen", "rosca", "fina", "gruesa", "plastico", "goma", "valvula"]
def desc(i):
    s = f"item{i} " + " ".join(rnd.choice(PAL) for _ in range(LARGO // 6))
    return s[:LARGO]
if os.environ.get("KANA"): PAL = ["ｶﾞｽ", "ﾈｼﾞ", "ﾅｯﾄ", "ﾜｯｼｬｰ", "ｹｰﾌﾞﾙ", "ﾊﾞﾙﾌﾞ", "ｺﾞﾑ", "ｽﾃﾝﾚｽ", "tornillo", "acero"]
DESCS = [desc(i) for i in range(2000)]
ITEMS = [{"descripcion": DESCS[i * 97]} for i in range(10)] + [{"descripcion": desc(5000 + i)} for i in range(10)]

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        await cs.save_products(db, "Proveedor Bench", [{"descripcion": d, "ncm": "8471.30.12"} for d in DESCS], owner_username="bench")
        for d in DESCS:
            await upsert_client_product_history(db, "bench", "cli-1", "84713012", d, origen="CHINA")
        await db.commit()
    tiempos = []
    for _ in range(3):
        async with AsyncSessionLocal() as db:
            cs.clave_de_producto.cache_clear() if hasattr(cs.clave_de_producto, "cache_clear") else None
            t = time.perf_counter()
            r = await cs.match_items(db, ITEMS, "Proveedor Bench", owner_username="bench")
            t1 = time.perf_counter()
            mems = [await lookup_client_memory(db, "bench", "cli-1", it["descripcion"]) for it in ITEMS]
            t2 = time.perf_counter()
        tiempos.append((t1 - t, t2 - t1))
    best = min(tiempos, key=lambda x: x[0] + x[1])
    ok_v = sum(1 for m in r["items_matched"] if m.get("match_type") != "none")
    ok_c = sum(1 for m in mems if m)
    print(f"largo={LARGO} proveedor={best[0]:.2f}s cliente={best[1]:.2f}s total={sum(best):.2f}s matches_prov={ok_v} matches_cli={ok_c}")
    os.unlink(path)
asyncio.run(main())
