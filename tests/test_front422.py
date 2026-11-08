"""Un 422 cuyo `detail` es la lista de pydantic se le muestra a la persona en
castellano, en cada pantalla que lee `detail`: nunca «[object Object]», el
texto genérico que tapa el motivo, ni el mensaje de pydantic en inglés.

Las pantallas corren de verdad en node (`front422_pantalla.js`) con el cuerpo
que devuelve el backend para cada entrada.
"""
import json
import pathlib
import subprocess

import pytest

from tests.test_entradas1 import CLAVES_MALAS, _post

ARNES = pathlib.Path(__file__).with_name("front422_pantalla.js")
PANTALLAS = ("api", "reset", "landing")
EN_INGLES = ("Field required", "should", "Value error", "Input", "JSON decode", "object Object", "Expecting")

# entrada → (ruta, cuerpo, lo que la persona tiene que leer)
ENTRADAS = {
    "falta_campo": ("/auth/login", b"{}", "Falta"),
    "no_es_json": ("/auth/login", b"nope", "JSON"),
    "tipo_equivocado": ("/auth/login", b'{"username": 1, "password": "x"}', "texto"),
    "no_es_objeto": ("/auth/login", b"[1]", "objeto"),
    "nombre_largo": ("/auth/register", {"username": "front422", "password": "Clave-larga-1",
                                        "email": "a@example.com", "name": "n" * 101}, "100"),
    "clave_73_bytes": ("/auth/reset-password", {"token": "t", "new_password": CLAVES_MALAS["73_bytes"]},
                       "72 bytes"),
}


def _pantalla(modo, status, cuerpo):
    salida = subprocess.run(["node", str(ARNES), modo, str(status), cuerpo],
                            capture_output=True, text=True, timeout=30)
    assert salida.returncode == 0, salida.stdout + salida.stderr
    return json.loads(salida.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("entrada", ENTRADAS)
@pytest.mark.parametrize("modo", PANTALLAS)
def test_el_422_de_pydantic_se_lee_en_castellano(modo, entrada):
    ruta, cuerpo, esperado = ENTRADAS[entrada]
    r = _post(ruta, cuerpo)
    assert r.status_code == 422 and isinstance(r.json()["detail"], list), r.text
    texto = _pantalla(modo, 422, r.text)["texto"]
    assert isinstance(texto, str), texto
    assert esperado in texto, texto
    assert not [p for p in EN_INGLES if p in texto], texto


@pytest.mark.parametrize("modo", PANTALLAS)
def test_un_detail_de_texto_se_muestra_tal_cual(modo):
    texto = _pantalla(modo, 400, json.dumps({"detail": "Ese email ya existe"}))["texto"]
    assert texto == "Ese email ya existe"
