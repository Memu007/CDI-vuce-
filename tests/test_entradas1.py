"""Un texto que llega de afuera no da 500 por no poder guardarse, hashearse o
repetirse en la respuesta de un pedido mal armado.

El NUL sólo rompe en Postgres: ese lado está en
`scripts/testing/entradas1_postgres.py`.
"""
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    CLAVE, CLAVE2, _bearer, _fila, _login, _sin_limites, _tablas, _usuario,
)
from tests.test_reset1 import _pedir_link, _usar_link
from proyecto_maria.main import app

SURROGATE = "Clave-1!\ud800"
NUL = "Clave-1!\x00x"
LARGA = "Clave-1!" + "ñ" * 33  # 74 bytes en UTF-8: bcrypt no la acepta
JUSTA = "Clave-1!" + "ñ" * 32  # 72 bytes: la más larga que entra


def _post(ruta, cuerpo, headers=None, tipo="application/json", metodo="POST"):
    """JSON en ASCII, como lo manda un navegador: así viaja un surrogate suelto."""
    contenido = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo).encode()
    cabeceras = {**({"Content-Type": tipo} if tipo else {}), **(headers or {})}
    cliente = TestClient(app, raise_server_exceptions=False)
    return cliente.request(metodo, ruta, content=contenido, headers=cabeceras)


def _sin_constantes(c):
    raise ValueError(f"{c} no es JSON")


def _json_valido(r):
    """El cuerpo leído como JSON estricto: en UTF-8 y sin NaN."""
    assert r.headers["content-type"] == "application/json", r.headers
    return json.loads(r.content.decode("utf-8"), parse_constant=_sin_constantes)


def _nuevo():
    return "ent1_" + uuid.uuid4().hex[:10]


def _por_reset(clave):
    _, mail = _usuario()
    token = _pedir_link(mail)
    r = _post("/auth/reset-password", {"token": token, "new_password": clave})
    return r, lambda: _usar_link(token, CLAVE2).status_code == 200


def _por_cambio(clave):
    u, _ = _usuario()
    r = _post("/api/user/change-password", {"current_password": CLAVE, "new_password": clave},
              _bearer(_login(u)))
    return r, lambda: _login(u, CLAVE) is not None


def _por_registro(clave):
    u = _nuevo()
    r = _post("/auth/register", {"username": u, "password": clave, "email": f"{u}@example.com", "name": "Ent"})
    return r, lambda: _fila(u) is None


def _por_estudio(clave):
    u = _nuevo()
    r = _post("/api/organizations/create",
              {"name": "Estudio", "username": u, "password": clave, "email": f"{u}@example.com"})
    return r, lambda: _fila(u) is None


VIAS = {"reset": _por_reset, "cambio": _por_cambio, "registro": _por_registro, "estudio": _por_estudio}
CLAVES_MALAS = {"surrogate": SURROGATE, "nul": NUL, "73_bytes_o_mas": LARGA}


@pytest.mark.parametrize("clave", CLAVES_MALAS, ids=list(CLAVES_MALAS))
@pytest.mark.parametrize("via", VIAS)
def test_clave_nueva_que_no_se_puede_hashear_da_422_y_no_cambia_nada(via, clave):
    r, nada_cambio = VIAS[via](CLAVES_MALAS[clave])
    assert r.status_code == 422, r.text
    assert "contraseña" in str(r.json()["detail"]), r.text
    # El link de reset sigue sirviendo, la clave vieja sigue y no se creó ninguna cuenta.
    assert nada_cambio()


@pytest.mark.parametrize("via", VIAS)
def test_clave_de_72_bytes_entra(via):
    """Contrapunto: el tope corta en el byte 73, no antes."""
    r, _ = VIAS[via](JUSTA)
    assert r.status_code == 200, r.text


TEXTOS_MALOS = {"surrogate": "Ent\ud800", "nul": "Ent\x00x"}


def _registro_con(campo, valor):
    u = _nuevo()
    cuerpo = {"username": u, "password": CLAVE, "email": f"{u}@example.com", "name": "Ent", campo: valor}
    return _post("/auth/register", cuerpo)


def _estudio_con(campo, valor):
    u = _nuevo()
    cuerpo = {"name": "Estudio", "username": u, "password": CLAVE, "email": f"{u}@example.com", campo: valor}
    return _post("/api/organizations/create", cuerpo)


def _perfil_con(campo, valor):
    u, _ = _usuario()
    return _post("/api/user/profile", {campo: valor, "current_password": CLAVE},
                 _bearer(_login(u)), metodo="PUT")


CAMPOS = {
    "registro_nombre": (_registro_con, "name"), "registro_invitacion": (_registro_con, "invite_token"),
    "registro_usuario": (_registro_con, "username"), "registro_email": (_registro_con, "email"),
    "registro_plan": (_registro_con, "plan"),
    "estudio_nombre": (_estudio_con, "name"), "estudio_usuario": (_estudio_con, "username"),
    "estudio_email": (_estudio_con, "email"),
    "perfil_nombre": (_perfil_con, "name"), "perfil_email": (_perfil_con, "email"),
}


@pytest.mark.parametrize("texto", TEXTOS_MALOS, ids=list(TEXTOS_MALOS))
@pytest.mark.parametrize("campo", CAMPOS)
def test_texto_del_alta_que_no_se_puede_guardar_no_da_500(campo, texto):
    alta, nombre = CAMPOS[campo]
    r = alta(nombre, TEXTOS_MALOS[texto])
    assert r.status_code < 500, r.text


def _mail_de(largo):
    return uuid.uuid4().hex + "a" * (largo - 32 - len("@example.com")) + "@example.com"


# Postgres no guarda un texto más largo que su columna y SQLite sí: acá se pide
# el rechazo claro. Cada uno tiene su contrapunto de un carácter menos.
LARGOS = {
    "registro_nombre": (_registro_con, "name", lambda n: "N" * n, 100),
    "registro_email": (_registro_con, "email", _mail_de, 100),
    "estudio_nombre": (_estudio_con, "name", lambda n: "N" * n, 200),
    "estudio_email": (_estudio_con, "email", _mail_de, 100),
    "perfil_email": (_perfil_con, "email", _mail_de, 100),
}


@pytest.mark.parametrize("campo", LARGOS)
def test_texto_mas_largo_que_su_columna_da_4xx_y_el_justo_entra(campo):
    alta, nombre, texto, tope = LARGOS[campo]
    r = alta(nombre, texto(tope + 1))
    assert r.status_code in (400, 422), r.text
    r = alta(nombre, texto(tope))
    assert r.status_code == 200, r.text


NO_UTF8 = b'{"username": "\xff\xfe", "password": 1}'
CUERPOS = {
    "no_utf8_texto": ("text/plain", NO_UTF8),
    "no_utf8_formulario": ("application/x-www-form-urlencoded", NO_UTF8),
    "no_utf8_sin_tipo": (None, NO_UTF8),
    "nan": ("application/json", b'{"username": NaN, "password": "x"}'),
    "infinito": ("application/json", b'{"username": Infinity, "password": -Infinity}'),
    "1e999": ("application/json", b'{"username": 1e999, "password": "x"}'),
}


@pytest.mark.parametrize("cuerpo", CUERPOS)
def test_el_422_de_un_cuerpo_raro_es_json_valido(cuerpo):
    tipo, contenido = CUERPOS[cuerpo]
    r = _post("/auth/login", contenido, tipo=tipo)
    assert r.status_code == 422, r.text
    datos = _json_valido(r)
    assert isinstance(datos["detail"], list) and datos["detail"], datos


CUERPOS_DE_GRUPO = {
    "agrupar_no_utf8": ("agrupar", b'{"item_ids": ["\xff\xfe", "b"]}'),
    "agrupar_no_json": ("agrupar", b"nope"),
    "agrupar_lista": ("agrupar", b"[1]"),
    "desagrupar_no_json": ("desagrupar", b"nope"),
    "desagrupar_lista": ("desagrupar", b"[1]"),
    "desagrupar_enorme": ("desagrupar", b'{"grupo_id": 100000000000000000000}'),
}


@pytest.mark.parametrize("cuerpo", CUERPOS_DE_GRUPO)
def test_agrupar_con_cuerpo_raro_da_4xx_en_json(cuerpo):
    ruta, contenido = CUERPOS_DE_GRUPO[cuerpo]
    u, _ = _usuario()
    r = _post(f"/api/operacion/no-existe/{ruta}", contenido, _bearer(_login(u)))
    assert 400 <= r.status_code < 500, r.text
    _json_valido(r)


def test_el_400_que_repite_texto_ajeno_en_una_lista_es_json_valido():
    u, _ = _usuario()
    r = _post("/generate_maria_export", {"operation_id": "x", "items": [], "comprador_pais": "Xx\ud800"},
              _bearer(_login(u)))
    assert r.status_code == 400, r.text
    assert "Xx" in json.dumps(_json_valido(r)["detail"]), r.text
