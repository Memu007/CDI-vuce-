"""ESTUDIO-1: el CUIT del despachante se carga por estudio y se elige en la
operación; va sólo al CDDTAGR.

Los estudios son de la cuenta, como los clientes: cada usuario ve, borra y
usa sólo los suyos. La operación manda `estudio_id`; sin él, el CUIT sale
como antes (`cuit_agr` y, si no viene, el del perfil). Se preselecciona el
último usado o el único. Todo con datos inventados y usuarios propios de
cada caso, con sesión de verdad (registro y login), sin override.
"""
import re
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria.main import app
from tests.test_maria7_rechazos_24_10 import _pedido

CUIT_PERFIL = "20111111112"
CUIT_A = "30222222223"
CUIT_B = "27333333334"


def _cddtagr(txt):
    return re.findall(r"^CDDTAGR=(.*?)\r?$", txt, re.M)


@pytest.fixture
def usuario(monkeypatch):
    """Da un TestClient con sesión propia de un usuario nuevo; los cierra al final."""
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setenv("DISABLE_DB_INIT", "true")
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setattr(limiter, "enabled", False)
    abiertos = []

    def _nuevo(cuit_perfil=""):
        c = TestClient(app)
        abiertos.append(c)
        nombre = f"estudio1_{uuid.uuid4().hex[:10]}"
        r = c.post("/auth/register", json={
            "username": nombre, "password": "Clave-Segura-123",
            "email": f"{nombre}@cdi.test", "name": nombre})
        assert r.status_code in (200, 201), r.text
        r = c.post("/auth/login", json={"username": nombre, "password": "Clave-Segura-123"})
        assert r.status_code == 200, r.text
        if cuit_perfil:
            r = c.put("/api/user/profile", json={"cuit": cuit_perfil})
            assert r.status_code == 200, r.text
        return c

    yield _nuevo
    for c in abiertos:
        c.close()


def _alta(c, nombre, cuit):
    r = c.post("/api/estudios", json={"nombre": nombre, "cuit": cuit})
    assert r.status_code == 200, r.text
    return r.json()["estudio"]


def _lista(c):
    r = c.get("/api/estudios")
    assert r.status_code == 200, r.text
    return r.json()


def _generar(c, estudio_id=None, cuit_agr=""):
    pedido = _pedido(cuit_agr=cuit_agr)
    if estudio_id is not None:
        pedido["estudio_id"] = estudio_id
    return c.post("/generate_maria", json=pedido)


# ------------------------------------------------------------ alta y lista


def test_el_alta_guarda_el_cuit_sin_guiones_y_lo_lista(usuario):
    a = usuario()
    est = _alta(a, "Estudio Inventado Uno", "30-22222222-3")
    assert est["cuit"] == CUIT_A and est["nombre"] == "Estudio Inventado Uno"
    datos = _lista(a)
    assert [(e["id"], e["cuit"]) for e in datos["estudios"]] == [(est["id"], CUIT_A)]


@pytest.mark.parametrize("cuit", ["3022222222", "302222222233", "30-2222222A-3", "", None, 30222222223])
def test_el_alta_rechaza_un_cuit_que_no_es_de_11_digitos(usuario, cuit):
    a = usuario()
    r = a.post("/api/estudios", json={"nombre": "Estudio Inventado", "cuit": cuit})
    assert r.status_code == 400, r.text
    assert "11 dígitos" in r.json()["detail"]
    assert _lista(a)["estudios"] == []


@pytest.mark.parametrize("nombre", ["", "   ", None, "Estudio\nInventado", "x" * 201])
def test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve(usuario, nombre):
    a = usuario()
    r = a.post("/api/estudios", json={"nombre": nombre, "cuit": CUIT_A})
    assert r.status_code == 400, r.text
    assert "nombre" in r.json()["detail"]
    assert _lista(a)["estudios"] == []


def test_el_mismo_cuit_dos_veces_en_la_cuenta_no_se_guarda(usuario):
    a = usuario()
    _alta(a, "Estudio Inventado Uno", CUIT_A)
    r = a.post("/api/estudios", json={"nombre": "Otro nombre", "cuit": "30-22222222-3"})
    assert r.status_code == 409, r.text
    assert len(_lista(a)["estudios"]) == 1


def test_el_mismo_cuit_en_otra_cuenta_si_se_guarda(usuario):
    a, b = usuario(), usuario()
    _alta(a, "Estudio Inventado Uno", CUIT_A)
    _alta(b, "Estudio Inventado Uno", CUIT_A)


# ------------------------------------------------------------- aislamiento


def test_otro_usuario_no_ve_ni_borra_ni_usa_los_estudios_ajenos(usuario):
    a = usuario(cuit_perfil=CUIT_PERFIL)
    b = usuario(cuit_perfil=CUIT_PERFIL)
    est = _alta(a, "Estudio Inventado de A", CUIT_A)

    assert _lista(b)["estudios"] == [] and _lista(b)["preseleccionado"] is None

    r = b.delete(f"/api/estudios/{est['id']}")
    assert r.status_code == 404, r.text

    # Ni para generar ni para los avisos: un error, no el CUIT de A ni el
    # respaldo del perfil en silencio.
    r = _generar(b, est["id"])
    assert r.status_code == 400, r.text
    assert CUIT_A not in r.text and "Estudio Inventado de A" not in r.text
    r = b.post("/generate_maria/avisos", json={**_pedido(cuit_agr=""), "estudio_id": est["id"]})
    assert r.status_code == 400, r.text
    assert CUIT_A not in r.text

    # A sigue teniendo el suyo, sin marcar como usado.
    datos = _lista(a)
    assert [e["id"] for e in datos["estudios"]] == [est["id"]]
    assert datos["estudios"][0]["ultimo_uso"] is None


def test_un_estudio_que_no_existe_da_error_y_no_cae_al_perfil(usuario):
    a = usuario(cuit_perfil=CUIT_PERFIL)
    r = _generar(a, str(uuid.uuid4()))
    assert r.status_code == 400, r.text
    assert "estudio" in r.text


def test_un_estudio_borrado_no_se_usa_mas(usuario):
    a = usuario(cuit_perfil=CUIT_PERFIL)
    est = _alta(a, "Estudio Inventado", CUIT_A)
    r = a.delete(f"/api/estudios/{est['id']}")
    assert r.status_code == 200, r.text
    assert _lista(a)["estudios"] == []
    assert _generar(a, est["id"]).status_code == 400


# ------------------------------------------------- el CUIT que va al TXT


def test_el_estudio_elegido_va_al_cddtagr_aunque_haya_perfil_y_cuit_agr(usuario):
    """La pantalla manda también el CUIT del perfil en `cuit_agr`: manda el estudio."""
    a = usuario(cuit_perfil=CUIT_PERFIL)
    est = _alta(a, "Estudio Inventado", CUIT_A)
    r = _generar(a, est["id"], cuit_agr=CUIT_PERFIL)
    assert r.status_code == 200, r.text
    txt = r.json()["content"]
    assert _cddtagr(txt) == [CUIT_A]
    # Va sólo al CDDTAGR: el nombre del estudio no entra al TXT.
    assert "Estudio Inventado" not in txt
    assert txt.count(CUIT_A) == 1


def test_sin_estudio_en_la_operacion_sigue_el_cuit_del_perfil(usuario):
    a = usuario(cuit_perfil=CUIT_PERFIL)
    _alta(a, "Estudio Inventado", CUIT_A)
    for estudio_id in (None, ""):
        r = _generar(a, estudio_id)
        assert r.status_code == 200, r.text
        assert _cddtagr(r.json()["content"]) == [CUIT_PERFIL]


def test_sin_estudio_ni_perfil_el_error_dice_donde_cargarlo(usuario):
    a = usuario()
    r = _generar(a)
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert "CDDTAGR" in detalle and "estudio" in detalle and "Mi perfil" in detalle
    r = a.post("/generate_maria/avisos", json=_pedido(cuit_agr=""))
    assert r.status_code == 200, r.text
    assert detalle in r.json()["avisos"]


def test_con_estudio_los_avisos_no_piden_el_cuit(usuario):
    a = usuario()
    est = _alta(a, "Estudio Inventado", CUIT_A)
    r = a.post("/generate_maria/avisos", json={**_pedido(cuit_agr=""), "estudio_id": est["id"]})
    assert r.status_code == 200, r.text
    assert not [x for x in r.json()["avisos"] if "CDDTAGR" in x]


# ------------------------------------------------------------ preselección


def test_se_preselecciona_el_unico(usuario):
    a = usuario()
    est = _alta(a, "Estudio Inventado", CUIT_A)
    assert _lista(a)["preseleccionado"] == est["id"]


def test_con_varios_se_preselecciona_el_ultimo_usado(usuario):
    a = usuario()
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    dos = _alta(a, "Estudio Inventado Dos", CUIT_B)
    # Varios y ninguno usado: no se elige por la persona.
    assert _lista(a)["preseleccionado"] is None

    assert _generar(a, dos["id"]).status_code == 200
    assert _lista(a)["preseleccionado"] == dos["id"]
    assert _generar(a, uno["id"]).status_code == 200
    assert _lista(a)["preseleccionado"] == uno["id"]


def test_los_avisos_y_un_txt_que_no_se_genera_no_cuentan_como_uso(usuario):
    a = usuario()
    uno = _alta(a, "Estudio Inventado Uno", CUIT_A)
    dos = _alta(a, "Estudio Inventado Dos", CUIT_B)
    assert _generar(a, uno["id"]).status_code == 200

    r = a.post("/generate_maria/avisos", json={**_pedido(cuit_agr=""), "estudio_id": dos["id"]})
    assert r.status_code == 200, r.text
    malo = {**_pedido(cuit_agr=""), "estudio_id": dos["id"], "moneda": ""}
    r = a.post("/generate_maria", json=malo)
    assert r.status_code == 400, r.text
    assert "CDDTAGR" not in r.text
    assert _lista(a)["preseleccionado"] == uno["id"]
