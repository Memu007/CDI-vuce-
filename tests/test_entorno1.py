"""Las puertas de desarrollo abren sólo con un ENVIRONMENT de desarrollo explícito.

Cada valor corre en un proceso aparte: las banderas de entorno se leen al
importar la app, y un monkeypatch de la bandera no prueba lo que pasa al
arrancar sin la variable.
"""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SONDA = REPO / "tests" / "entorno_sonda.py"
AUSENTE = None
CERRADOS = [AUSENTE, "", "production", "prod", "staging", "Development", " development", "TESTING"]
ABIERTOS = ["development", "test", "testing"]

IMPORTAR_SIN_ENV = "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; import proyecto_maria.main"

pytestmark = pytest.mark.security


def _sondear(valor, carpeta: Path) -> dict:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(REPO), "HOME": str(carpeta),
        "DATABASE_URL": f"sqlite+aiosqlite:///{carpeta}/sonda.db",
        "JWT_SECRET_KEY": "clave-larga-de-cuarenta-y-dos-caracteres-para-prueba-xx",
        "ALLOWED_ORIGINS": "http://cdi.example.com", "FRONTEND_URL": "http://cdi.example.com",
        "GEMINI_API_KEY": "test-key", "VUCE_MODE": "fake", "TARIFAR_MODE": "fake", "AFIP_MODE": "fake",
        "DOLARAPI_BASE": "http://127.0.0.1:9/v1/dolares",
    }
    if valor is not AUSENTE:
        env["ENVIRONMENT"] = valor
    proc = subprocess.run([sys.executable, str(SONDA)], capture_output=True, text=True,
                          cwd=str(carpeta), env=env, timeout=120)
    salida = proc.stdout + proc.stderr
    linea = [l for l in proc.stdout.splitlines() if l.startswith("SONDA ")]
    assert proc.returncode == 0 and linea, f"ENVIRONMENT={valor!r}: la sonda no terminó\n{salida[-3000:]}"
    datos = json.loads(linea[-1][len("SONDA "):])
    datos["link_en_salida"] = bool(datos["token"]) and datos["token"] in salida.replace(linea[-1], "")
    # Sin JWT_SECRET_KEY la app usaría la clave de desarrollo, que está en el repositorio.
    del env["JWT_SECRET_KEY"]
    arranque = subprocess.run([sys.executable, "-c", IMPORTAR_SIN_ENV], capture_output=True, text=True,
                              cwd=str(carpeta), env=env, timeout=120)
    datos["arranca_sin_clave"] = arranque.returncode == 0
    datos["rechaza_sin_clave"] = "insecure JWT_SECRET_KEY" in arranque.stderr
    return datos


@pytest.fixture(scope="module")
def sondas(tmp_path_factory):
    # En paralelo: once arranques seguidos pueden pasar el tope de tiempo de la prueba.
    valores = CERRADOS + ABIERTOS
    with ThreadPoolExecutor(max_workers=4) as pool:
        datos = pool.map(lambda v: _sondear(v, tmp_path_factory.mktemp("entorno")), valores)
    return dict(zip(valores, datos))


def _estado(abierta: bool, cerrada: bool) -> str:
    # Una respuesta que no es ni la abierta ni la cerrada no cuenta como cerrada.
    return "abierta" if abierta else "cerrada" if cerrada else "sin medir"


PUERTAS = {
    "demo": lambda d: _estado(d["demo"] == ["basico", "demo", "premium"], d["demo"] == []),
    "login_con_lo_guardado": lambda d: _estado(d["login_hash"] == 200, d["login_hash"] == 401),
    "webhook_sin_secreto": lambda d: _estado(d["firma"] is True, d["firma"] is False),
    "link_de_reset_en_stdout": lambda d: _estado(bool(d["token"]) and d["link_en_salida"],
                                                 bool(d["token"]) and not d["link_en_salida"]),
    "cobro_simulado": lambda d: _estado(d["cobro"] == 200, d["cobro"] == 404),
    "clave_jwt_de_desarrollo": lambda d: _estado(d["arranca_sin_clave"], d["rechaza_sin_clave"]),
}


def _distintos(sondas, puerta, valores, esperado):
    return {v: e for v in valores if (e := PUERTAS[puerta](sondas[v])) != esperado}


@pytest.mark.parametrize("puerta", PUERTAS)
def test_puerta_cerrada_fuera_de_desarrollo(sondas, puerta):
    otros = _distintos(sondas, puerta, CERRADOS, "cerrada")
    assert not otros, f"{puerta} no queda cerrada: {otros!r}"


@pytest.mark.parametrize("puerta", PUERTAS)
def test_puerta_abierta_en_desarrollo(sondas, puerta):
    """Contrapunto: la prueba distingue, porque en desarrollo la puerta sigue."""
    otros = _distintos(sondas, puerta, ABIERTOS, "abierta")
    assert not otros, f"{puerta} no queda abierta: {otros!r}"
