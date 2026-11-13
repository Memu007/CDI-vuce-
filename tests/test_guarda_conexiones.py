"""La guarda de conexiones de conftest.py, corrida de verdad en un pytest aparte.

Cada dato es una sesión de pytest que carga el conftest.py real. Si alguien
rompe el reconocimiento, la foto de antes del test, el veredicto del cierre o
el chequeo de arranque, algún dato cambia de resultado.
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

GUARDA = Path(__file__).with_name("conftest.py")
RAIZ = GUARDA.parent.parent

CARGAR_GUARDA = """
import importlib.util
_spec = importlib.util.spec_from_file_location("guarda_real", {ruta!r})
guarda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guarda)
{ajuste}
globals().update({{k: v for k, v in vars(guarda).items() if not k.startswith("__")}})
"""

FUGA_EN_EL_TEST = """
import aiosqlite
abiertas = []

async def test_deja_una_abierta():
    abiertas.append(await aiosqlite.connect(":memory:"))
"""

FUGA_EN_UN_FIXTURE = """
import aiosqlite
import pytest
abiertas = []

@pytest.fixture
async def conexion():
    abiertas.append(await aiosqlite.connect(":memory:"))

def test_usa_el_fixture(conexion):
    pass
"""

CIERRA_BIEN = """

async def test_abre_y_cierra():
    async with aiosqlite.connect(":memory:") as conexion:
        await conexion.execute("select 1")
"""

FUGA = "dejó 1 conexión(es) de aiosqlite abiertas"
CIEGA = "La guarda de conexiones no ve una conexión abierta"

# (qué se prueba, test de adentro, nombre del hilo que busca la guarda, rc, debe decir, no debe decir)
DATOS = [
    ("veredicto del cierre", FUGA_EN_EL_TEST, None, 1, FUGA, None),
    ("foto antes de los fixtures", FUGA_EN_UN_FIXTURE, None, 1, FUGA, None),
    ("la culpa es de quien la deja", FUGA_EN_EL_TEST + CIERRA_BIEN, None, 1,
     "test_deja_una_abierta dejó 1", "test_abre_y_cierra dejó"),
    ("chequeo de arranque", FUGA_EN_EL_TEST, "(otro_hilo)", 4, CIEGA, "passed"),
]


@pytest.mark.parametrize(
    "inner,hilo,rc,dice,no_dice", [d[1:] for d in DATOS], ids=[d[0] for d in DATOS]
)
def test_guarda_de_conexiones(tmp_path, inner, hilo, rc, dice, no_dice):
    ajuste = f"guarda._HILO_AIOSQLITE = {hilo!r}" if hilo else ""
    (tmp_path / "conftest.py").write_text(CARGAR_GUARDA.format(ruta=str(GUARDA), ajuste=ajuste))
    (tmp_path / "test_adentro.py").write_text(textwrap.dedent(inner))
    (tmp_path / "pytest.ini").write_text("[pytest]\nasyncio_mode = auto\n")
    env = {**os.environ, "PYTHONPATH": str(RAIZ)}
    corrida = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "--rootdir", str(tmp_path),
         "-c", str(tmp_path / "pytest.ini"), str(tmp_path)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=110,
    )
    salida = corrida.stdout + corrida.stderr
    assert corrida.returncode == rc, salida
    assert dice in salida, salida
    assert no_dice is None or no_dice not in salida, salida
