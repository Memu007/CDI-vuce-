"""OBSERVABILIDAD-1: `api_logs.owner_username` aparece sola al arrancar.

Una base creada antes de que el modelo tuviera la columna no la recibe de
`create_all`, y cada métrica se pierde con UndefinedColumn. El arranque
agrega la columna (nullable, sin tocar filas) y su índice, no hace nada si
ya están, y si falla deja el motivo en el log sin frenar la app.

Acá va SQLite, llamando a la migración contra una base propia de cada
prueba. El arranque entero (uvicorn, en SQLite y en Postgres 16) está en
`scripts/testing/observabilidad1_arranque.py`.
"""
import asyncio
import logging

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from proyecto_maria import main
from proyecto_maria.database import connection
from proyecto_maria.database.models import APILog, Base

# api_logs como la dejó una versión vieja: todas las columnas menos el dueño.
TABLA_VIEJA = """
CREATE TABLE api_logs (
    id VARCHAR PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    client_ip VARCHAR(45),
    user_agent TEXT,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    operation_id VARCHAR,
    external_api VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"""
FILAS_VIEJAS = """
INSERT INTO api_logs (id, endpoint, method, status_code, response_time_ms, error_message, created_at)
VALUES ('vieja-1', '/robots.txt', 'GET', 200, 4, NULL, '2026-10-24 10:00:00'),
       ('vieja-2', '/api/clientes', 'POST', 500, 31, 'falló algo ñandú', '2026-10-24 10:01:00')"""


@pytest.fixture()
def base(tmp_path, monkeypatch):
    """Una SQLite descartable por prueba, puesta como motor de la app sólo
    mientras dura la prueba: no toca test.db."""
    motor = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'obs1.db'}")
    monkeypatch.setattr(connection, "engine", motor)
    monkeypatch.setattr(connection, "IS_SQLITE", True)

    def sql(*consultas):
        async def correr():
            async with motor.begin() as c:
                salida = None
                for q in consultas:
                    r = await c.exec_driver_sql(q)
                    salida = [tuple(f) for f in r.fetchall()] if r.returns_rows else None
                return salida
        return asyncio.run(correr())

    yield motor, sql
    asyncio.run(motor.dispose())


def migrar():
    asyncio.run(main._migrate_add_api_logs_owner_column())


def columnas(sql):
    # (nombre, tipo, notnull, default)
    return {f[1]: (f[2], f[3], f[4]) for f in sql("PRAGMA table_info(api_logs)")}


def indices_del_dueno(sql):
    nombres = [f[1] for f in sql("PRAGMA index_list(api_logs)")]
    return sorted(n for n in nombres
                  if [f[2] for f in sql(f'PRAGMA index_info("{n}")')][:1] == ["owner_username"])


def esquema(sql):
    return sql("SELECT type, name, sql FROM sqlite_master ORDER BY type, name")


def filas(sql):
    return sql("SELECT * FROM api_logs ORDER BY id")


def test_base_vieja_recibe_columna_nullable_con_indice_y_conserva_filas(base):
    _, sql = base
    sql(TABLA_VIEJA, FILAS_VIEJAS)
    antes = filas(sql)
    assert "owner_username" not in columnas(sql)

    migrar()

    cols = columnas(sql)
    assert cols.get("owner_username") == ("VARCHAR(50)", 0, None), \
        f"la columna tiene que quedar VARCHAR(50), nullable y sin default: {cols.get('owner_username')}"
    assert indices_del_dueno(sql) == ["ix_api_logs_owner_username"], \
        f"tiene que quedar un índice sobre owner_username: {indices_del_dueno(sql)}"
    # Las filas viejas, enteras y sin dueño inventado.
    assert [f[:-1] for f in filas(sql)] == antes, "las filas viejas cambiaron"
    assert sql("SELECT id, owner_username FROM api_logs ORDER BY id") == [
        ("vieja-1", None), ("vieja-2", None)], "a las filas viejas no se les inventa dueño"


def test_correrla_dos_veces_no_cambia_nada(base):
    _, sql = base
    sql(TABLA_VIEJA, FILAS_VIEJAS)
    migrar()
    esquema1, filas1 = esquema(sql), filas(sql)
    migrar()
    assert esquema(sql) == esquema1, "la segunda corrida cambió el esquema"
    assert filas(sql) == filas1, "la segunda corrida cambió filas"


def test_la_metrica_se_graba_despues_de_migrar(base):
    motor, sql = base
    sql(TABLA_VIEJA, FILAS_VIEJAS)
    migrar()

    async def grabar():
        # Lo mismo que graba MetricsMiddleware.
        async with AsyncSession(motor) as s:
            s.add(APILog(endpoint="/robots.txt", method="GET", client_ip="127.0.0.1",
                         status_code=200, response_time_ms=3, error_message=None))
            await s.commit()
    asyncio.run(grabar())
    assert sql("SELECT endpoint, owner_username FROM api_logs WHERE id NOT LIKE 'vieja-%'") == [
        ("/robots.txt", None)]


def test_base_nueva_de_create_all_queda_igual(base):
    motor, sql = base

    async def crear():
        async with motor.begin() as c:
            await c.run_sync(Base.metadata.create_all, tables=[APILog.__table__])
    asyncio.run(crear())
    antes = esquema(sql)
    migrar()
    assert esquema(sql) == antes, "en una base nueva no hay nada que agregar"


def test_indice_del_script_viejo_con_otro_nombre_no_se_duplica(base):
    # migrate_add_owner.py dejaba la columna con el índice ix_api_logs_owner.
    _, sql = base
    sql(TABLA_VIEJA, "ALTER TABLE api_logs ADD COLUMN owner_username VARCHAR(50)",
        "CREATE INDEX ix_api_logs_owner ON api_logs (owner_username)")
    antes = esquema(sql)
    migrar()
    assert esquema(sql) == antes, f"duplicó el índice: {indices_del_dueno(sql)}"


def test_columna_sin_indice_recibe_el_indice(base):
    _, sql = base
    sql(TABLA_VIEJA, "ALTER TABLE api_logs ADD COLUMN owner_username VARCHAR(50)", FILAS_VIEJAS)
    migrar()
    assert indices_del_dueno(sql) == ["ix_api_logs_owner_username"]


def test_sin_tabla_no_crea_nada_ni_se_queja(base, caplog):
    # Primer arranque de una base vacía: la tabla la crea create_all.
    _, sql = base
    caplog.set_level(logging.WARNING)
    migrar()
    assert esquema(sql) == []
    assert not [r for r in caplog.records if "OBSERVABILIDAD-1" in r.getMessage()], caplog.text


def test_si_falla_no_levanta_y_deja_el_motivo_en_el_log(base, caplog):
    # api_logs es una vista: SQLite no le deja agregar columnas.
    _, sql = base
    sql("CREATE TABLE logs_reales (id VARCHAR PRIMARY KEY, endpoint VARCHAR(200))",
        "CREATE VIEW api_logs AS SELECT id, endpoint FROM logs_reales")
    caplog.set_level(logging.WARNING)
    migrar()  # no levanta
    registros = [r for r in caplog.records if "OBSERVABILIDAD-1" in r.getMessage()]
    assert registros, f"la falla no quedó en el log: {caplog.text!r}"
    assert registros[0].levelno >= logging.WARNING
    assert registros[0].exc_info, "el log tiene que traer el motivo (la excepción)"
