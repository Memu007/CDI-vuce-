"""Contadores de intentos contra abuso (ABUSO-1), en la tabla `limites_auth`.

Un solo camino, haya o no Redis: la base es la misma para todos los workers y
sobrevive a los reinicios. El engine se toma de `connection` en cada uso
(las pruebas lo reemplazan después de importar la app). Cada escritura va en su propia transacción, así el
intento queda contado aunque la ruta después conteste 401, y es un único
INSERT ... ON CONFLICT DO UPDATE ... RETURNING: dos pedidos simultáneos no
leen la misma cuenta. Antes de escribir se borran las filas vencidas.
"""
import time

from sqlalchemy import case, delete, select

from proyecto_maria.database import connection as _conn
from proyecto_maria.database.connection import IS_SQLITE
from proyecto_maria.database.models import LimiteAuth

_T = LimiteAuth.__table__


def _ahora() -> float:
    return time.time()


def _insert():
    if IS_SQLITE:
        from sqlalchemy.dialects.sqlite import insert as _ins
    else:
        from sqlalchemy.dialects.postgresql import insert as _ins
    return _ins(_T)


async def purgar_vencidas() -> None:
    async with _conn.engine.begin() as conn:
        await conn.execute(delete(_T).where(_T.c.vence <= _ahora()))


async def segundos_bloqueado(clave: str) -> int:
    """Segundos que le quedan al bloqueo de `clave`; 0 si no está bloqueada."""
    ahora = _ahora()
    async with _conn.engine.connect() as conn:
        hasta = (await conn.execute(
            select(_T.c.bloqueado_hasta).where(_T.c.clave == clave, _T.c.vence > ahora)
        )).scalar()
    return max(1, int(hasta - ahora)) if hasta and hasta > ahora else 0


async def sumar_fallo(clave: str, tope: int = 5, bloqueo: float = 15 * 60,
                      olvido: float = 24 * 3600) -> int:
    """Suma un fallo. Desde el fallo número `tope` cada fallo bloquea por
    `bloqueo` segundos; la cuenta se olvida tras `olvido` segundos sin fallos."""
    ahora = _ahora()
    ins = _insert().values(clave=clave, cuenta=1, bloqueado_hasta=0.0, vence=ahora + olvido)
    ins = ins.on_conflict_do_update(index_elements=[_T.c.clave], set_={
        "cuenta": _T.c.cuenta + 1,
        "vence": ahora + olvido,
        "bloqueado_hasta": case((_T.c.cuenta + 1 >= tope, ahora + bloqueo), else_=_T.c.bloqueado_hasta),
    }).returning(_T.c.cuenta)
    async with _conn.engine.begin() as conn:
        await conn.execute(delete(_T).where(_T.c.vence <= ahora))
        return (await conn.execute(ins)).scalar_one()


async def contar(clave: str, ventana: float) -> int:
    """Suma un pedido en una ventana fija de `ventana` segundos que arranca
    con el primero, y devuelve cuántos van (este incluido)."""
    ahora = _ahora()
    ins = _insert().values(clave=clave, cuenta=1, bloqueado_hasta=0.0, vence=ahora + ventana)
    ins = ins.on_conflict_do_update(index_elements=[_T.c.clave], set_={
        "cuenta": _T.c.cuenta + 1,
    }).returning(_T.c.cuenta)
    async with _conn.engine.begin() as conn:
        await conn.execute(delete(_T).where(_T.c.vence <= ahora))
        return (await conn.execute(ins)).scalar_one()


async def limpiar(clave: str) -> None:
    async with _conn.engine.begin() as conn:
        await conn.execute(delete(_T).where(_T.c.clave == clave))
