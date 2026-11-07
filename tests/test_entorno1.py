"""Las puertas de desarrollo abren sólo con un ENVIRONMENT de desarrollo explícito.

Cada valor corre en un proceso aparte: las banderas de entorno se leen al
importar la app, y un monkeypatch de la bandera no prueba lo que pasa al
arrancar sin la variable.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SONDA = REPO / "tests" / "entorno_sonda.py"
AUSENTE = None
CERRADOS = [AUSENTE, "", "production", "prod", "staging", "Development", " development", "TESTING"]
ABIERTOS = ["development", "test", "testing"]

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
    return datos


@pytest.fixture(scope="module")
def sondas(tmp_path_factory):
    return {v: _sondear(v, tmp_path_factory.mktemp("entorno")) for v in CERRADOS + ABIERTOS}


PUERTAS = {
    "demo": lambda d: bool(d["demo"]),
    "login_con_lo_guardado": lambda d: d["login_hash"] == 200,
    "webhook_sin_secreto": lambda d: d["firma"] is True,
    "link_de_reset_en_stdout": lambda d: d["link_en_salida"],
    "cobro_simulado": lambda d: d["cobro"] != 404,
}


@pytest.mark.parametrize("puerta", PUERTAS)
def test_puerta_cerrada_fuera_de_desarrollo(sondas, puerta):
    abiertas = [v for v in CERRADOS if PUERTAS[puerta](sondas[v])]
    assert not abiertas, f"{puerta} abre con ENVIRONMENT en {abiertas!r}"


@pytest.mark.parametrize("puerta", PUERTAS)
def test_puerta_abierta_en_desarrollo(sondas, puerta):
    """Contrapunto: la prueba distingue, porque en desarrollo la puerta sigue."""
    cerradas = [v for v in ABIERTOS if not PUERTAS[puerta](sondas[v])]
    assert not cerradas, f"{puerta} no abre con ENVIRONMENT en {cerradas!r}"
