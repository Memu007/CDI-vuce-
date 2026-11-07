"""Contadores de intentos contra abuso (ABUSO-1), en la tabla `limites_auth`.

Un solo camino, haya o no Redis: la base es la misma para todos los workers y
sobrevive a los reinicios. Cada función usa la sesión del pedido y hace
commit, así el intento queda contado aunque la ruta después conteste 401 y el
pedido nunca toma una segunda conexión del pool: hay que llamarlas antes de
cambiar nada. Contar es un único INSERT ... ON CONFLICT DO UPDATE ...
RETURNING: dos pedidos simultáneos no leen la misma cuenta. Antes de escribir
se borran las filas vencidas.
"""
import hashlib
import time

from sqlalchemy import and_, case, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from proyecto_maria.database import connection as _conn
from proyecto_maria.database.connection import IS_SQLITE
from proyecto_maria.database.models import LimiteAuth

_T = LimiteAuth.__table__


def _ahora() -> float:
    return time.time()


def _clave(clave: str) -> str:
    """La columna tiene 120 caracteres y la IP sale de X-Forwarded-For, que
    puede traer cualquier cosa: una clave más larga se guarda como su comienzo
    y su sha256, que la sigue distinguiendo."""
    if len(clave) <= 120:
        return clave
    return clave[:50] + ":" + hashlib.sha256(clave.encode()).hexdigest()


def _insert():
    if IS_SQLITE:
        from sqlalchemy.dialects.sqlite import insert as _ins
    else:
        from sqlalchemy.dialects.postgresql import insert as _ins
    return _ins(_T)


async def purgar_vencidas() -> None:
    async with _conn.engine.begin() as conn:
        await conn.execute(delete(_T).where(_T.c.vence <= _ahora()))


async def _escribir(db: AsyncSession, ahora: float, consulta) -> int:
    await db.execute(delete(_T).where(_T.c.vence <= ahora))
    cuenta = (await db.execute(consulta)).scalar_one()
    await db.commit()
    return cuenta


async def segundos_bloqueado(db: AsyncSession, clave: str) -> int:
    """Segundos que le quedan al bloqueo de `clave`; 0 si no está bloqueada."""
    clave = _clave(clave)
    ahora = _ahora()
    hasta = (await db.execute(
        select(_T.c.bloqueado_hasta).where(_T.c.clave == clave, _T.c.vence > ahora)
    )).scalar()
    await db.commit()
    return max(1, int(hasta - ahora)) if hasta and hasta > ahora else 0


async def sumar_fallo(db: AsyncSession, clave: str, tope: int = 5, bloqueo: float = 15 * 60,
                      olvido: float = 24 * 3600) -> int:
    """Suma un fallo y devuelve la cuenta. Desde el fallo número `tope` cada
    fallo bloquea por `bloqueo` segundos; la cuenta se olvida tras `olvido`
    segundos sin fallos. Vencido un bloqueo, la cuenta vuelve a `tope`: pasa
    uno y bloquea de nuevo. Así, más de `tope` quiere decir que el fallo llegó
    con el bloqueo puesto, aunque haya pasado el chequeo previo a la vez que
    otros."""
    clave = _clave(clave)
    ahora = _ahora()
    vencido = and_(_T.c.bloqueado_hasta > 0, _T.c.bloqueado_hasta <= ahora)
    nueva = case((vencido, tope), else_=_T.c.cuenta + 1)
    ins = _insert().values(clave=clave, cuenta=1, bloqueado_hasta=0.0, vence=ahora + olvido)
    ins = ins.on_conflict_do_update(index_elements=[_T.c.clave], set_={
        "cuenta": nueva,
        "vence": ahora + olvido,
        "bloqueado_hasta": case((nueva >= tope, ahora + bloqueo), else_=_T.c.bloqueado_hasta),
    }).returning(_T.c.cuenta)
    return await _escribir(db, ahora, ins)


async def contar(db: AsyncSession, clave: str, ventana: float) -> int:
    """Suma un pedido en una ventana fija de `ventana` segundos que arranca
    con el primero, y devuelve cuántos van (este incluido)."""
    clave = _clave(clave)
    ahora = _ahora()
    ins = _insert().values(clave=clave, cuenta=1, bloqueado_hasta=0.0, vence=ahora + ventana)
    ins = ins.on_conflict_do_update(index_elements=[_T.c.clave], set_={
        "cuenta": _T.c.cuenta + 1,
    }).returning(_T.c.cuenta)
    return await _escribir(db, ahora, ins)


async def limpiar(db: AsyncSession, clave: str) -> None:
    await db.execute(delete(_T).where(_T.c.clave == _clave(clave)))
    await db.commit()


async def descontar(db: AsyncSession, clave: str, propia: str) -> None:
    """Perdona en `clave` sólo lo contado en `propia`; el DELETE ... RETURNING
    evita restar dos veces si dos llamadas corren a la vez."""
    clave, propia = _clave(clave), _clave(propia)
    ahora = _ahora()
    await db.execute(delete(_T).where(_T.c.vence <= ahora))
    n = (await db.execute(delete(_T).where(_T.c.clave == propia).returning(_T.c.cuenta))).scalar() or 0
    if n:
        await db.execute(update(_T).where(_T.c.clave == clave).values(
            cuenta=_T.c.cuenta - n,
            bloqueado_hasta=case((_T.c.bloqueado_hasta <= ahora, 0.0), else_=_T.c.bloqueado_hasta)))
        await db.execute(delete(_T).where(_T.c.clave == clave, _T.c.cuenta <= 0))
    await db.commit()
