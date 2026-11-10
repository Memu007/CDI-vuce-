"""Un link para restablecer la contraseña sirve una sola vez y deja de servir
cuando el dueño cambia la clave o el email, o usa otro link.

Dos usos a la vez del mismo link, y un cambio de email a la vez que el reset
o que el pedido del link, están contra Postgres en
`scripts/testing/reset1_postgres.py`.
"""
import pytest

from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    CLAVE, CLAVE2, CLAVE3, _bearer, _consulta, _fila, _http, _login, _sin_limites, _tablas, _usuario,
)
from proyecto_maria.database.models import PasswordResetToken
from proyecto_maria.main import guardar_si_la_clave_sigue, hash_password, verify_password


def _pedir_link(mail):
    r = _http().post("/auth/request-password-reset", json={"email": mail})
    assert r.status_code == 200, r.text
    return r.json()["dev_token_hint"]


def _usar_link(token, nueva):
    return _http().post("/auth/reset-password", json={"token": token, "new_password": nueva})


def _cambia_la_clave(u, mail, token):
    r = _http().post("/api/user/change-password", headers=_bearer(_login(u)),
                     json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200, r.text
    return CLAVE2


def _cambia_el_email(u, mail, token):
    r = _http().put("/api/user/profile", headers=_bearer(_login(u)),
                    json={"email": "otro_" + mail, "current_password": CLAVE})
    assert r.status_code == 200, r.text
    return CLAVE


def _usa_otro_link(u, mail, token):
    assert _usar_link(_pedir_link(mail), CLAVE2).status_code == 200
    return CLAVE2


def _usa_el_mismo_link(u, mail, token):
    assert _usar_link(token, CLAVE2).status_code == 200
    return CLAVE2


CAMBIOS = {"cambio de clave": _cambia_la_clave, "cambio de email": _cambia_el_email,
           "otro reset": _usa_otro_link, "el mismo link dos veces": _usa_el_mismo_link}


@pytest.mark.parametrize("cambio", CAMBIOS)
def test_el_link_no_sirve_despues_de_un_cambio(cambio):
    u, mail = _usuario()
    token = _pedir_link(mail)
    vigente = CAMBIOS[cambio](u, mail, token)

    r = _usar_link(token, CLAVE3)
    assert r.status_code == 400, f"{cambio}: el link viejo sigue sirviendo ({r.status_code} {r.text[:120]})"
    assert r.json()["detail"] == "Token inválido o expirado"
    hash_guardado = _fila(u).password
    assert verify_password(vigente, hash_guardado) and not verify_password(CLAVE3, hash_guardado), \
        f"{cambio}: la clave cambió con el link viejo"


def test_un_link_nuevo_despues_del_cambio_sirve():
    """Lo que muere es el link de antes, no la recuperación de la cuenta."""
    u, mail = _usuario()
    _cambia_la_clave(u, mail, None)
    r = _usar_link(_pedir_link(mail), CLAVE3)
    assert r.status_code == 200, r.text
    assert verify_password(CLAVE3, _fila(u).password)


def test_un_link_que_vence_antes_de_guardar_no_cambia_la_clave():
    """El reset valida el link y después calcula el hash: si vence en el medio, no se guarda."""
    u, mail = _usuario()
    token = _pedir_link(mail)
    hash_actual = _fila(u).password

    async def vencer_y_guardar(s):
        await s.execute(update(PasswordResetToken).where(PasswordResetToken.token == token)
                        .values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
        return await guardar_si_la_clave_sigue(s, u, hash_actual, consumir=token, password=hash_password(CLAVE3))

    assert _consulta(vencer_y_guardar) is False
    assert verify_password(CLAVE, _fila(u).password)
