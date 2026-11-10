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
# Un aviso de pago sin secreto no se puede verificar: tampoco abre en desarrollo.
SIEMPRE_CERRADAS = ["webhook_sin_secreto"]

SIN_DOTENV = "import dotenv; dotenv.load_dotenv = lambda *a, **k: False; "
IMPORTAR_SIN_ENV = SIN_DOTENV + "import proyecto_maria.main"
IMPORTAR_SIN_BASE = SIN_DOTENV + "import proyecto_maria.database.connection"

pytestmark = pytest.mark.security


def _sondear(valor, carpeta: Path) -> dict:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(REPO), "HOME": str(carpeta),
        "DATABASE_URL": f"sqlite+aiosqlite:///{carpeta}/sonda.db",
        "JWT_SECRET_KEY": "clave-larga-de-cuarenta-y-dos-caracteres-para-prueba-xx",
        "ALLOWED_ORIGINS": "http://cdi.example.com", "FRONTEND_URL": "http://cdi.example.com",
        "GEMINI_API_KEY": "test-key", "VUCE_MODE": "fake", "TARIFAR_MODE": "fake", "AFIP_MODE": "fake",
        "DOLARAPI_BASE": "http://127.0.0.1:9/v1/dolares",
        # Desde el arranque, para que una lectura de la bandera al importar también cuente.
        "ENABLE_SIMULATE_CHARGE": "true",
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
    env["JWT_SECRET_KEY"] = "clave-larga-de-cuarenta-y-dos-caracteres-para-prueba-xx"
    del env["DATABASE_URL"]
    base = subprocess.run([sys.executable, "-c", IMPORTAR_SIN_BASE], capture_output=True, text=True,
                          cwd=str(carpeta), env=env, timeout=120)
    datos["arranca_sin_base"] = base.returncode == 0
    datos["rechaza_sin_base"] = "ENVIRONMENT no es de desarrollo" in base.stderr
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{carpeta}/sonda.db"
    del env["ALLOWED_ORIGINS"]
    origenes = subprocess.run([sys.executable, "-c", IMPORTAR_SIN_ENV], capture_output=True, text=True,
                              cwd=str(carpeta), env=env, timeout=120)
    datos["arranca_sin_origenes"] = origenes.returncode == 0
    datos["rechaza_sin_origenes"] = "CORS config error" in origenes.stderr
    env["ALLOWED_ORIGINS"] = "http://cdi.example.com"
    del env["FRONTEND_URL"]
    frontend = subprocess.run([sys.executable, "-c", IMPORTAR_SIN_ENV], capture_output=True, text=True,
                              cwd=str(carpeta), env=env, timeout=120)
    datos["arranca_sin_frontend"] = frontend.returncode == 0
    datos["rechaza_sin_frontend"] = "FRONTEND_URL no esta seteada" in frontend.stderr
    return datos


@pytest.fixture(scope="module")
def sondas(tmp_path_factory):
    # En paralelo: once arranques seguidos pueden pasar el tope de tiempo de la prueba.
    # Las carpetas van antes del pool: mktemp no aguanta hilos en paralelo.
    valores = CERRADOS + ABIERTOS
    carpetas = [tmp_path_factory.mktemp("entorno") for _ in valores]
    with ThreadPoolExecutor(max_workers=4) as pool:
        datos = pool.map(_sondear, valores, carpetas)
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
    # Con ENABLE_SIMULATE_CHARGE puesta: la bandera no abre el cobro fuera de desarrollo.
    "cobro_simulado": lambda d: _estado(d["cobro"] == 200, d["cobro"] == 404),
    "clave_jwt_de_desarrollo": lambda d: _estado(d["arranca_sin_clave"], d["rechaza_sin_clave"]),
    "csrf_que_solo_avisa": lambda d: _estado(d["csrf"] == 404, d["csrf"] == 403),
    "cookies_sin_secure": lambda d: _estado(d["cookies"] == {"access_token": False, "csrf_token": False},
                                            d["cookies"] == {"access_token": True, "csrf_token": True}),
    "docs_y_openapi": lambda d: _estado(d["docs"] == [200, 200, 200], d["docs"] == [404, 404, 404]),
    "sqlite_sin_database_url": lambda d: _estado(d["arranca_sin_base"], d["rechaza_sin_base"]),
    "vuce_simulado": lambda d: _estado(d["vuce"] == "responde", d["vuce"] == "SourceUnavailableError"),
    # Los links de los emails y la vuelta del cobro salen de la misma URL.
    "frontend_en_localhost": lambda d: _estado(d["frontend"] == ["http://127.0.0.1:8010"] * 6,
                                               d["frontend"] == ["rechaza"] * 6),
    "arranca_sin_frontend_url": lambda d: _estado(d["arranca_sin_frontend"], d["rechaza_sin_frontend"]),
    "origenes_de_localhost": lambda d: _estado(d["arranca_sin_origenes"], d["rechaza_sin_origenes"]),
    "sin_hsts": lambda d: _estado(not d["hsts"], d["hsts"]),
    "sin_limite_desde_127": lambda d: _estado(d["limite_127"] == 200, d["limite_127"] == 429),
}


def _distintos(sondas, puerta, valores, esperado):
    return {v: e for v in valores if (e := PUERTAS[puerta](sondas[v])) != esperado}


@pytest.mark.parametrize("puerta", PUERTAS)
def test_puerta_cerrada_fuera_de_desarrollo(sondas, puerta):
    otros = _distintos(sondas, puerta, CERRADOS, "cerrada")
    assert not otros, f"{puerta} no queda cerrada: {otros!r}"


@pytest.mark.parametrize("puerta", SIEMPRE_CERRADAS)
def test_puerta_cerrada_tambien_en_desarrollo(sondas, puerta):
    otros = _distintos(sondas, puerta, ABIERTOS, "cerrada")
    assert not otros, f"{puerta} no queda cerrada: {otros!r}"


@pytest.mark.parametrize("puerta", [p for p in PUERTAS if p not in SIEMPRE_CERRADAS])
def test_puerta_abierta_en_desarrollo(sondas, puerta):
    """Contrapunto: la prueba distingue, porque en desarrollo la puerta sigue."""
    otros = _distintos(sondas, puerta, ABIERTOS, "abierta")
    assert not otros, f"{puerta} no queda abierta: {otros!r}"
