"""Candados de la cuenta que paga, compartidos por main y los routers."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from proyecto_maria.database.models import Organization, User


async def cuenta_bloqueada(db: AsyncSession, username: str):
    """Bloquea usuario y organización, siempre en ese orden, hasta el commit o rollback.
    populate_existing: sin él, valen los contadores que get_current_user leyó antes del lock.
    NO KEY: no choca con el KEY SHARE que toma un insert con clave foránea a estas filas.
    of=: sin él, SQLAlchemy reusa el FOR UPDATE que otra consulta igual dejó en su cache."""
    result = await db.execute(
        select(User)
        .where(User.username == username)
        .with_for_update(key_share=True, of=User)
        .execution_options(populate_existing=True)
    )
    db_user = result.scalars().first()
    if not db_user:
        return None
    if db_user.organization_id:
        result = await db.execute(
            select(Organization)
            .where(Organization.id == db_user.organization_id)
            .with_for_update(key_share=True, of=Organization)
            .execution_options(populate_existing=True)
        )
        org = result.scalars().first()
        if org:
            return db_user, org
    return db_user, db_user
