"""Regresión VUCE-1 · G1.5: sin DATABASE_URL en producción, la app no arranca.

Contexto (ROADMAP-REVIEW, `PROPUESTA-G1-G7.md`): el fallback a SQLite en
`database/connection.py` era incondicional. En Railway el disco del contenedor es
efímero, así que arrancar producción sin `DATABASE_URL` levantaba una base SQLite
que se borra en cada deploy — se perdería la base de todos los estudios con un
`warning` que nadie mira.

Criterio de cierre G1.5: con ENVIRONMENT=production y sin DATABASE_URL, el proceso
termina con error, no con un warning. Los casos G1.1–G1.4 (JWT y CORS) ya cortan.

Cada caso se corre en un subproceso: la config de base se resuelve al importar el
módulo, una sola vez por proceso.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SECRETO_OK = "clave-larga-de-cuarenta-y-dos-caracteres-para-test-xx"


def _importar(env: dict) -> subprocess.CompletedProcess:
    """Importa el módulo de conexión en un proceso limpio con el entorno dado."""
    base = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO_ROOT), "HOME": "/tmp"}
    base.update(env)
    return subprocess.run(
        [sys.executable, "-c", "import proyecto_maria.database.connection"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), env=base, timeout=60,
    )


@pytest.mark.security
def test_produccion_sin_database_url_no_arranca():
    """G1.5: el proceso tiene que terminar con error, no caer a SQLite."""
    proc = _importar({"ENVIRONMENT": "production"})  # sin DATABASE_URL
    assert proc.returncode != 0, (
        "La app arrancó en producción sin DATABASE_URL. Salida:\n"
        + (proc.stdout + proc.stderr)[-2000:]
    )
    assert "DATABASE_URL" in (proc.stdout + proc.stderr), (
        "Cortó, pero el mensaje no menciona DATABASE_URL"
    )
    assert "sqlite" not in (proc.stdout + proc.stderr).lower() or "no" in (proc.stdout + proc.stderr).lower(), (
        "El mensaje sugiere que igual cayó a SQLite"
    )


@pytest.mark.security
def test_produccion_con_database_url_arranca():
    """Contrapunto: con DATABASE_URL puesta, importa sin error."""
    proc = _importar({
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    })
    assert proc.returncode == 0, (
        "La app no importó con DATABASE_URL válida. Salida:\n"
        + (proc.stdout + proc.stderr)[-2000:]
    )


@pytest.mark.security
def test_desarrollo_sin_database_url_sigue_cayendo_a_sqlite():
    """En desarrollo el fallback a SQLite es válido y no debe cortar."""
    proc = _importar({"ENVIRONMENT": "development"})  # sin DATABASE_URL
    assert proc.returncode == 0, (
        "En desarrollo, sin DATABASE_URL, debería caer a SQLite y no cortar. Salida:\n"
        + (proc.stdout + proc.stderr)[-2000:]
    )
