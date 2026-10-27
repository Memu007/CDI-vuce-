"""ESTUDIO-1b: lo que quedó de ESTUDIO-1 (D23 b y la revisión de la PM).

1. Generar con el CUIT del perfil también cuenta como «último usado»: la
   preselección es lo último que se usó, estudio o perfil. Un estudio único
   sin usar gana sólo si el perfil nunca se usó.
2. `estudio_id` vacío es sólo `""` o la falta del campo. «null», «None»,
   «N/A», espacios, un null de JSON o un número no caen al perfil: 400.
3. El nombre del estudio no puede verse vacío ni dar vuelta el texto:
   espacios de ancho cero y controles de dirección dan 400.

Mismo arnés que `test_estudio1.py`: usuarios propios de cada caso, con
sesión de verdad y datos inventados.
"""
import pytest

from tests.test_estudio1 import (  # noqa: F401  (usuario es un fixture)
    CUIT_A, CUIT_B, CUIT_PERFIL, _alta, _cddtagr, _generar, _lista, usuario,
)
from tests.test_maria7_rechazos_24_10 import _pedido


# ------------------------------------------------------------ 1. D23 (b)


def test_generar_con_el_perfil_despues_de_un_estudio_preselecciona_el_perfil(usuario):
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    r = _generar(a, uno["id"])
    assert r.status_code == 200, r.text
    assert _lista(a)["preseleccionado"] == uno["id"]

    r = _generar(a, "")
    assert r.status_code == 200, r.text
    assert _cddtagr(r.json()["content"]) == [CUIT_PERFIL]
    assert _lista(a)["preseleccionado"] is None

    # Y vuelve al estudio cuando se lo usa otra vez.
    assert _generar(a, uno["id"]).status_code == 200
    assert _lista(a)["preseleccionado"] == uno["id"]


def test_sin_el_campo_estudio_id_tambien_cuenta_como_uso_del_perfil(usuario):
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _generar(a, uno["id"]).status_code == 200
    r = _generar(a)   # sin estudio_id
    assert r.status_code == 200, r.text
    assert _lista(a)["preseleccionado"] is None


def test_un_estudio_unico_sin_uso_del_perfil_gana(usuario):
    """Recién cargado y sin ningún TXT con el perfil antes: viene elegido."""
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _lista(a)["preseleccionado"] == uno["id"]


def test_un_estudio_unico_cargado_despues_de_usar_el_perfil_no_gana(usuario):
    """Lo último usado es el perfil: cargar un estudio no es usarlo."""
    a = usuario(CUIT_PERFIL)
    assert _generar(a, "").status_code == 200
    _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _lista(a)["preseleccionado"] is None


def test_con_varios_usados_el_perfil_mas_reciente_gana(usuario):
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    dos = _alta(a, "Estudio Inventado Dos", CUIT_B)
    assert _generar(a, uno["id"]).status_code == 200
    assert _generar(a, dos["id"]).status_code == 200
    assert _generar(a, "").status_code == 200
    assert _lista(a)["preseleccionado"] is None
    assert _generar(a, uno["id"]).status_code == 200
    assert _lista(a)["preseleccionado"] == uno["id"]


def test_el_cuit_del_perfil_en_cuit_agr_cuenta_como_uso_del_perfil(usuario):
    """La pantalla manda el CUIT del perfil en `cuit_agr` (finalize.js)."""
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _generar(a, uno["id"]).status_code == 200
    r = _generar(a, "", cuit_agr="20-11111111-2")
    assert r.status_code == 200, r.text
    assert _cddtagr(r.json()["content"]) == [CUIT_PERFIL]
    assert _lista(a)["preseleccionado"] is None


def test_un_cuit_agr_propio_no_cuenta_como_uso_del_perfil(usuario):
    """Con `cuit_agr` en el pedido el CDDTAGR no es el del perfil."""
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _generar(a, uno["id"]).status_code == 200
    r = _generar(a, "", cuit_agr=CUIT_B)
    assert r.status_code == 200, r.text
    assert _cddtagr(r.json()["content"]) == [CUIT_B]
    assert _lista(a)["preseleccionado"] == uno["id"]


def test_los_avisos_y_un_txt_que_no_sale_con_el_perfil_no_cuentan(usuario):
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _generar(a, uno["id"]).status_code == 200

    r = a.post("/generate_maria/avisos", json={**_pedido(cuit_agr=""), "estudio_id": ""})
    assert r.status_code == 200, r.text
    r = a.post("/generate_maria", json={**_pedido(cuit_agr=""), "estudio_id": "", "moneda": ""})
    assert r.status_code == 400, r.text
    assert _lista(a)["preseleccionado"] == uno["id"]


def test_el_uso_del_perfil_es_de_cada_cuenta(usuario):
    a = usuario(CUIT_PERFIL)
    b = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    otro = _alta(b, "Estudio Inventado Otro", CUIT_A)
    assert _generar(a, uno["id"]).status_code == 200
    assert _generar(b, otro["id"]).status_code == 200
    assert _generar(b, "").status_code == 200
    assert _lista(b)["preseleccionado"] is None
    assert _lista(a)["preseleccionado"] == uno["id"]


# ------------------------------------------------------------ 2. estudio_id


@pytest.mark.parametrize("estudio_id", ["null", "None", "N/A", "none", "  ", "\t", None, 0, ["x"]])
@pytest.mark.parametrize("ruta", ["/generate_maria", "/generate_maria/avisos"])
def test_un_estudio_id_escrito_como_vacio_da_400_y_no_cae_al_perfil(usuario, ruta, estudio_id):
    a = usuario(CUIT_PERFIL)
    _alta(a, "Estudio Inventado Uno", CUIT_A)
    r = a.post(ruta, json={**_pedido(cuit_agr=""), "estudio_id": estudio_id})
    assert r.status_code == 400, r.text
    assert "estudio" in r.json()["detail"]
    assert "CDDTAGR=" not in r.text


def test_un_estudio_id_con_espacios_alrededor_da_400(usuario):
    a = usuario(CUIT_PERFIL)
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    r = _generar(a, f" {uno['id']} ")
    assert r.status_code == 400, r.text


@pytest.mark.parametrize("ruta", ["/generate_maria", "/generate_maria/avisos"])
def test_un_estudio_id_vacio_sigue_con_el_perfil(usuario, ruta):
    a = usuario(CUIT_PERFIL)
    _alta(a, "Estudio Inventado Uno", CUIT_A)
    r = a.post(ruta, json={**_pedido(cuit_agr=""), "estudio_id": ""})
    assert r.status_code == 200, r.text
    if ruta == "/generate_maria":
        assert _cddtagr(r.json()["content"]) == [CUIT_PERFIL]


# ------------------------------------------------------------ 3. nombre


@pytest.mark.parametrize("nombre", [
    "​",                       # sólo un espacio de ancho cero
    "​‌‍ ⁠",    # todo invisible
    "﻿",
    "Estudio​Inventado",
    "Estudio Inventado‎",
    "Estudio Inventado‏",
    "‮odatnevnI oidutsE",      # al revés
    "Estudio ‪Inventado",
    "Estudio ‬Inventado",
    "Estudio ⁦Inventado⁩",
    "Estudio ⁧Inventado",
    "Estudio ⁨Inventado",
    "Estudio ؜Inventado",
])
def test_el_alta_rechaza_un_nombre_invisible_o_al_reves(usuario, nombre):
    a = usuario()
    r = a.post("/api/estudios", json={"nombre": nombre, "cuit": CUIT_A})
    assert r.status_code == 400, r.text
    assert "nombre" in r.json()["detail"]
    assert _lista(a)["estudios"] == []


@pytest.mark.parametrize("nombre", ["Estudio Peña & Asociados", "Estudio «Ñandú» S.R.L.", "Estudio 中文"])
def test_el_alta_acepta_un_nombre_con_acentos_y_otros_alfabetos(usuario, nombre):
    a = usuario()
    est = _alta(a, nombre, CUIT_A)
    assert est["nombre"] == nombre


def test_sin_cuit_en_el_perfil_su_uso_viejo_no_cuenta(usuario):
    """Si el perfil ya no tiene CUIT, elegirlo deja la operación sin CUIT del
    despachante: el estudio único vuelve a venir elegido."""
    a = usuario(CUIT_PERFIL)
    assert _generar(a, "").status_code == 200
    assert a.put("/api/user/profile", json={"cuit": ""}).status_code == 200
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    assert _lista(a)["preseleccionado"] == uno["id"]
