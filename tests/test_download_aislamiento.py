"""Regresión: /download solo entrega archivos del usuario que los generó.

Hallazgo original (ronda G3 del plan adversarial, 2026-07-26): el nombre del
MARIA.TXT sale del número de factura (`MARIA_FAC_0001-00012345.TXT`), que es
corto y adivinable. Como `/download/{filename}` buscaba directo en `DATA_DIR`
y solo verificaba que hubiera sesión, cualquier usuario registrado podía
bajarse la declaración de otro despachante —con CUIT del importador, NCM y
valores— probando números de factura. Lo mismo con cualquier otro archivo
suelto en `DATA_DIR` (por ejemplo `ncm_historial_<usuario>.json`).

Arreglo: los archivos descargables viven en una carpeta por usuario y
`/download` resuelve únicamente dentro de la del que pide.
"""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria.main import (  # noqa: E402
    DATA_DIR,
    app,
    get_current_user,
    _user_downloads_dir,
)


# No hace falta disparar el lifespan de la app: `conftest.pytest_sessionstart`
# ya crea las tablas, y estos tests no tocan la base (autenticación por
# override + archivos en disco). Arrancar el lifespan acá dejaba hilos vivos
# que impedían que pytest terminara.


@pytest.fixture
def como():
    """Devuelve una función que da un TestClient autenticado como X.

    Cierra los clientes y limpia el override al terminar: si quedan abiertos,
    el proceso de pytest no termina nunca (ver deuda de la ronda G5).
    """
    abiertos = []

    def _factory(username: str):
        c = _build_client(username)
        abiertos.append(c)
        return c

    yield _factory

    for c in abiertos:
        c.close()
    app.dependency_overrides.pop(get_current_user, None)


def _build_client(username: str):
    """Devuelve un TestClient autenticado como `username`."""
    usuario = {
        "username": username,
        "name": username,
        "email": f"{username}@test.cdi",
        "cuit": "",
        "plan": "premium",
        "is_verified": True,
        "billing_status": "active",
        "trial_ends_at": None,
        "default_aduana_codigo": "",
        "default_puerto_destino": "",
        "default_tipo_destinacion": "",
        "team_owner_username": None,
        "effective_owner": username,
        "roles": [],
    }
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    app.dependency_overrides[get_current_user] = lambda: usuario
    return TestClient(app)


CONTENIDO = "[DDT]\r\nNDDTIMMIOE=30712345678\r\n"
NOMBRE = "MARIA_FAC_0001-00012345.TXT"


def test_ana_baja_su_propio_archivo(como):
    """El caso feliz: el dueño sí puede descargar lo que generó."""
    ruta = os.path.join(_user_downloads_dir("ana"), NOMBRE)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(CONTENIDO)

    resp = como("ana").get(f"/download/{NOMBRE}")

    assert resp.status_code == 200
    assert "30712345678" in resp.text


def test_beto_no_baja_el_archivo_de_ana(como):
    """El ataque original: adivinar el nro de factura de otro despachante."""
    ruta = os.path.join(_user_downloads_dir("ana"), NOMBRE)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(CONTENIDO)

    resp = como("beto").get(f"/download/{NOMBRE}")

    assert resp.status_code == 404, (
        "Beto se bajó el MARIA.TXT de Ana: fuga de datos entre despachantes"
    )
    assert "30712345678" not in resp.text


def test_no_se_bajan_archivos_internos_de_data_dir(como):
    """Antes /download servía cualquier archivo suelto en DATA_DIR."""
    interno = os.path.join(DATA_DIR, "ncm_historial_ana.json")
    with open(interno, "w", encoding="utf-8") as f:
        f.write('{"secreto": "historial de Ana"}')

    try:
        resp = como("beto").get("/download/ncm_historial_ana.json")
        assert resp.status_code == 404
        assert "secreto" not in resp.text
    finally:
        os.remove(interno)


def test_path_traversal_sigue_bloqueado(como):
    """El basename ya recortaba el path; queda cubierto igual."""
    resp = como("beto").get("/download/..%2F..%2F.env")
    assert resp.status_code in (403, 404)


def test_carpetas_de_usuarios_distintos_no_se_pisan():
    """Dos usuarios no pueden terminar apuntando a la misma carpeta."""
    assert _user_downloads_dir("ana") != _user_downloads_dir("beto")
    # El nombre de usuario no queda expuesto en el filesystem.
    assert "ana" not in os.path.basename(_user_downloads_dir("ana"))
