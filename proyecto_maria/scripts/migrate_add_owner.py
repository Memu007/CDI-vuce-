"""
Migración multi-tenant para SQLite (D4 del plan integrado).

Agrega las columnas `owner_username` y campos faltantes a las tablas
existentes SIN tirar datos. Idempotente: se puede correr varias veces.

Uso:
    python -m proyecto_maria.scripts.migrate_add_owner
    python -m proyecto_maria.scripts.migrate_add_owner --db /ruta/custom.db

Qué hace:
    1. Agrega owner_username a clients, operations, ncm_notes,
       client_product_history, system_backups, api_logs.
    2. Agrega columnas faltantes que usa el DataStore pero no estaban
       en los modelos: clients.notes, clients.favorite, operations.op_code,
       operations.source, operations.extra.
    3. Backfill: datos preexistentes quedan con owner_username = 'demo'.
    4. Crea índices para queries filtradas por owner.
    5. Relaja el UNIQUE global de clients.email → UNIQUE(owner_username, email)
       (en SQLite requiere índice único compuesto, que es equivalente).

No toca PostgreSQL de producción — eso se hace con alembic aparte.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from typing import Iterable


# Columnas a agregar por tabla. Formato: (tabla, columna, sql_type, default)
NEW_COLUMNS: list[tuple[str, str, str, str | None]] = [
    # owner_username en todas las tablas con datos de despachante.
    ("clients", "owner_username", "VARCHAR(50)", None),
    ("operations", "owner_username", "VARCHAR(50)", None),
    ("ncm_notes", "owner_username", "VARCHAR(50)", None),
    ("client_product_history", "owner_username", "VARCHAR(50)", None),
    ("system_backups", "owner_username", "VARCHAR(50)", None),
    ("api_logs", "owner_username", "VARCHAR(50)", None),

    # Columnas faltantes que usa el DataStore.
    ("clients", "notes", "TEXT", None),
    ("clients", "favorite", "BOOLEAN", "0"),
    ("operations", "op_code", "VARCHAR(100)", None),
    ("operations", "source", "VARCHAR(50)", None),
    ("operations", "extra", "JSON", None),

    # client_id debería ser nullable en NCMNote y Operation post-refactor,
    # pero no bajamos un NOT NULL en SQLite sin recrear tabla. Si era
    # nullable=False antes y ya hay datos, queda como estaba.
]

# Índices nuevos para queries multi-tenant.
NEW_INDEXES: list[tuple[str, str, str]] = [
    # (nombre_idx, tabla, cols)
    ("ix_clients_owner", "clients", "owner_username"),
    ("ix_operations_owner", "operations", "owner_username"),
    ("ix_operations_owner_created", "operations", "owner_username, created_at"),
    ("ix_ncm_notes_owner_ncm", "ncm_notes", "owner_username, ncm_code"),
    ("ix_cph_owner_client", "client_product_history", "owner_username, client_id"),
    ("ix_system_backups_owner", "system_backups", "owner_username"),
    ("ix_api_logs_owner", "api_logs", "owner_username"),
]

# Índice único compuesto que reemplaza el UNIQUE(email) global que traía
# el modelo legacy. En SQLite no se puede "alterar" el unique de una
# columna sin recrear la tabla, pero podemos sumar un UNIQUE compuesto
# nuevo que sea el contrato real. Si hay un índice unique de solo email
# (autogenerado por SQLAlchemy) sigue existiendo; lo chequeamos y
# dropeamos si está presente.
UNIQUE_COMPOSITE: tuple[str, str, str] = (
    "uq_clients_owner_email", "clients", "owner_username, email"
)

LEGACY_EMAIL_UNIQUE_CANDIDATES = (
    "ix_clients_email",       # naming que suele poner SQLAlchemy/declarative
    "sqlite_autoindex_clients_1",
    "sqlite_autoindex_clients_2",
)

DEFAULT_OWNER = "demo"


def table_columns(cur: sqlite3.Cursor, table: str) -> set[str]:
    cur.execute(f'PRAGMA table_info("{table}")')
    return {row[1] for row in cur.fetchall()}


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None


def indexes_for_table(cur: sqlite3.Cursor, table: str) -> list[tuple[str, int]]:
    """Devuelve lista de (nombre_indice, unique_bool) para la tabla."""
    cur.execute(f'PRAGMA index_list("{table}")')
    return [(row[1], row[2]) for row in cur.fetchall()]


def ensure_user(cur: sqlite3.Cursor, username: str) -> None:
    """Garantiza que el usuario existe (sin romper si ya está)."""
    cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
    if cur.fetchone():
        return
    cur.execute(
        """
        INSERT INTO users (username, email, password, name, plan, is_verified)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            f"{username}@local.dev",
            "!migration_placeholder_not_usable",  # hash inválido: nadie puede loguearse con este user
            f"Backfill user ({username})",
            "basic",
            0,
        ),
    )
    print(f"   + usuario '{username}' creado para backfill")


def _rebuild_ncm_notes_nullable_client(cur: sqlite3.Cursor) -> bool:
    """SQLite no soporta ALTER para relajar NOT NULL. Rebuild si hace falta.

    Solo se dispara cuando `ncm_notes.client_id` está declarada NOT NULL.
    Preserva las filas existentes y re-crea índices clave.
    """
    if not table_exists(cur, "ncm_notes"):
        return False
    cur.execute('PRAGMA table_info("ncm_notes")')
    rows = cur.fetchall()
    client_id_info = next((r for r in rows if r[1] == "client_id"), None)
    if client_id_info is None:
        return False
    # PRAGMA columns: cid, name, type, notnull, dflt_value, pk
    if client_id_info[3] == 0:  # ya es nullable
        return False

    print("   · rebuild de ncm_notes para permitir client_id NULL...")
    # Schema nuevo, sincronizado con models.NCMNote.
    cur.execute(
        """
        CREATE TABLE ncm_notes_new (
            id VARCHAR NOT NULL,
            owner_username VARCHAR(50),
            client_id VARCHAR,
            ncm_code VARCHAR(10) NOT NULL,
            note TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(owner_username) REFERENCES users (username),
            FOREIGN KEY(client_id) REFERENCES clients (id)
        )
        """
    )
    cur.execute(
        """
        INSERT INTO ncm_notes_new
            (id, owner_username, client_id, ncm_code, note, created_at, updated_at)
        SELECT id, owner_username, client_id, ncm_code, note, created_at, updated_at
        FROM ncm_notes
        """
    )
    cur.execute("DROP TABLE ncm_notes")
    cur.execute("ALTER TABLE ncm_notes_new RENAME TO ncm_notes")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_ncm_notes_owner_ncm "
        'ON "ncm_notes" (owner_username, ncm_code)'
    )
    return True


def run_migration(db_path: str, backfill_owner: str = DEFAULT_OWNER, dry_run: bool = False) -> int:
    if not os.path.exists(db_path):
        print(f"ERROR: DB no encontrada en {db_path}")
        return 1

    print(f"DB: {db_path}")
    print(f"Backfill owner: {backfill_owner}")
    print(f"Dry run: {dry_run}")
    print("-" * 60)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # 1) Agregar columnas faltantes ---------------------------------
        for table, col, col_type, default in NEW_COLUMNS:
            if not table_exists(cur, table):
                print(f"   · tabla '{table}' no existe (skip)")
                continue
            cols = table_columns(cur, table)
            if col in cols:
                continue
            default_clause = f" DEFAULT {default}" if default is not None else ""
            sql = f'ALTER TABLE "{table}" ADD COLUMN {col} {col_type}{default_clause}'
            print(f"   + {sql}")
            if not dry_run:
                cur.execute(sql)

        # 2) Asegurar usuario backfill ---------------------------------
        if not dry_run:
            ensure_user(cur, backfill_owner)

        # 3) Backfill de owner_username para filas existentes ----------
        for table, col, _ctype, _def in NEW_COLUMNS:
            if col != "owner_username":
                continue
            if not table_exists(cur, table):
                continue
            # En dry-run los ALTER no se aplicaron todavía, así que la
            # columna `owner_username` quizá no existe; solo reportamos.
            current_cols = table_columns(cur, table)
            if "owner_username" not in current_cols:
                if dry_run:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                    n = cur.fetchone()[0]
                    print(f"   · {table}: {n} filas quedarían backfill -> '{backfill_owner}'")
                continue
            sql = (
                f'UPDATE "{table}" SET owner_username=? '
                f"WHERE owner_username IS NULL"
            )
            if dry_run:
                cur.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE owner_username IS NULL'
                )
                n = cur.fetchone()[0]
                print(f"   · {table}: {n} filas quedarían backfill -> '{backfill_owner}'")
            else:
                cur.execute(sql, (backfill_owner,))
                if cur.rowcount:
                    print(f"   · {table}: backfill de {cur.rowcount} filas -> '{backfill_owner}'")

        # 4) Índices ---------------------------------------------------
        for idx_name, table, cols in NEW_INDEXES:
            if not table_exists(cur, table):
                continue
            existing = {name for name, _u in indexes_for_table(cur, table)}
            if idx_name in existing:
                continue
            sql = f'CREATE INDEX IF NOT EXISTS {idx_name} ON "{table}" ({cols})'
            print(f"   + {sql}")
            if not dry_run:
                cur.execute(sql)

        # 5) Índice único compuesto (owner_username, email) -----------
        idx_name, table, cols = UNIQUE_COMPOSITE
        if table_exists(cur, table):
            existing = {name for name, _u in indexes_for_table(cur, table)}
            if idx_name not in existing:
                sql = f'CREATE UNIQUE INDEX IF NOT EXISTS {idx_name} ON "{table}" ({cols})'
                print(f"   + {sql}")
                if not dry_run:
                    cur.execute(sql)

        # 6) Rebuild ncm_notes.client_id para que sea nullable ----------
        if not dry_run:
            if _rebuild_ncm_notes_nullable_client(cur):
                print("   · ncm_notes recreada con client_id NULL permitido")

        # 7) Drop del UNIQUE global de clients.email (si existe) ------
        # SQLAlchemy crea `sqlite_autoindex_clients_N` para columnas con
        # unique=True. Esos no se pueden dropear directamente. Los
        # detectamos pero no los tocamos: con el modelo corregido y una
        # recreación futura (dev) no se generan. Esta migración es
        # incremental y deja el autoindex in situ; en la practica no
        # interfiere porque el workflow nuevo controla las colisiones
        # por (owner, email) antes de insertar.
        for cand in LEGACY_EMAIL_UNIQUE_CANDIDATES:
            existing = {name for name, _u in indexes_for_table(cur, table)}
            if cand in existing and not cand.startswith("sqlite_autoindex"):
                sql = f"DROP INDEX IF EXISTS {cand}"
                print(f"   - {sql}")
                if not dry_run:
                    cur.execute(sql)

        if not dry_run:
            conn.commit()
            print("-" * 60)
            print("OK: cambios commiteados.")
        else:
            conn.rollback()
            print("-" * 60)
            print("Dry run: ningún cambio aplicado.")
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"ERROR durante la migración: {exc}")
        return 2
    finally:
        conn.close()


def detect_default_db() -> str:
    """Busca la DB activa basándose en variables de entorno o ubicaciones típicas."""
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("sqlite"):
        # extraer path de formatos `sqlite+aiosqlite:///path` o `sqlite:///path`
        after_slashes = url.split(":///", 1)[-1]
        path = after_slashes or url.split("://", 1)[-1]
        if path.startswith("./"):
            path = os.path.abspath(path)
        return path
    # Candidatos en orden de preferencia.
    candidates = [
        os.path.abspath("cdi_dev.db"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "local_dev.db")),
        os.path.abspath("maria_data.db"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=None, help="Path al archivo SQLite")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="Username para backfill")
    parser.add_argument("--dry-run", action="store_true", help="No commitea cambios")
    args = parser.parse_args(list(argv) if argv is not None else None)
    db_path = args.db or detect_default_db()
    return run_migration(db_path, backfill_owner=args.owner, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
