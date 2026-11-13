"""El CUIT del despachante que guarda «Mi perfil» es un CUIT: once dígitos y el
último, el verificador. De ahí sale el CDDTAGR del TXT.

Lo mismo en el navegador: `scripts/testing/pantalla_cuit_perfil1.js`.
"""
import pytest

from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    _bearer, _fila, _http, _login, _poner, _sin_limites, _tablas, _usuario,
)

BUENO = "20111111112"
# lo que llega → por qué no es un CUIT
MALOS = {
    "20999999998": "verificador equivocado",
    "20-11111111-3": "verificador equivocado, con guiones",
    "30712345670": "verificador equivocado, de una empresa",
    "２０１１１１１１１１２": "dígitos de ancho completo",
    "2011111111": "diez dígitos",
    "201111111120": "doce dígitos",
}
# lo que llega → lo que queda guardado
BUENOS = {
    "20-11111111-2": BUENO, " 20 11111111 2 ": BUENO, "20.11111111.2": BUENO,
    "30-71234567-1": "30712345671", "": None,
}


def _cuenta(**guardado):
    """Una cuenta nueva con esos campos puestos directo en la base, y su sesión."""
    u, _ = _usuario()
    if guardado:
        _poner(u, **guardado)
    return u, _bearer(_login(u))


def _guardar(sesion, **campos):
    return _http().put("/api/user/profile", json=campos, headers=sesion)


@pytest.mark.parametrize("cuit", MALOS, ids=list(MALOS.values()))
def test_lo_que_no_es_un_cuit_no_se_guarda(cuit):
    u, sesion = _cuenta(cuit=BUENO, name="Antes")
    r = _guardar(sesion, name="Después", cuit=cuit)
    assert r.status_code == 400, f"{MALOS[cuit]}: {r.status_code} {r.text}"
    assert "CUIT" in r.json()["detail"], r.text
    fila = _fila(u)
    assert (fila.cuit, fila.name) == (BUENO, "Antes"), "el pedido rechazado no deja nada guardado"


@pytest.mark.parametrize("cuit", BUENOS, ids=[repr(c) for c in BUENOS])
def test_un_cuit_bueno_se_guarda_sin_separadores(cuit):
    u, sesion = _cuenta(cuit="30712345671" if BUENOS[cuit] == BUENO else BUENO)
    r = _guardar(sesion, cuit=cuit)
    assert r.status_code == 200, r.text
    assert r.json()["profile"]["cuit"] == (BUENOS[cuit] or "")
    assert _fila(u).cuit == BUENOS[cuit]


def test_uno_malo_que_ya_estaba_guardado_queda_hasta_que_se_corrige():
    viejo = "20999999998"
    u, sesion = _cuenta(cuit=viejo)
    assert _http().get("/api/user/profile", headers=sesion).json()["profile"]["cuit"] == viejo

    # Sin el CUIT en el pedido, el resto del perfil se guarda y el CUIT no se toca.
    assert _guardar(sesion, name="Sin tocar el CUIT").status_code == 200
    assert (_fila(u).cuit, _fila(u).name) == (viejo, "Sin tocar el CUIT")

    # La pantalla manda siempre el CUIT que muestra: con el malo, pide corregirlo.
    r = _guardar(sesion, name="Con el malo", cuit=viejo)
    assert r.status_code == 400 and "CUIT" in r.json()["detail"], r.text
    assert (_fila(u).cuit, _fila(u).name) == (viejo, "Sin tocar el CUIT")

    assert _guardar(sesion, name="Corregido", cuit=BUENO).status_code == 200
    assert (_fila(u).cuit, _fila(u).name) == (BUENO, "Corregido")
