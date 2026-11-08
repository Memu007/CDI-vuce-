"""La destinación que va al ISTA, y el seguro borrado de vuelta a FOB.

1. Sólo un código de 4 letras o números ASCII llega al TXT: lo demás da 400,
   en importación y en exportación, en vez de salir cortado o corrupto.
2. Una exportación no acepta una destinación de importación.
3. Un texto enorme no se normaliza entero.
4. Con el seguro borrado y de vuelta a FOB, el 400 dice lo que pasó.
5. El lector de PDF rechaza la exportación con lo invisible adelante, y lo
   que no es un código lo deja vacío.
6. El perfil sólo guarda como default un código de importación.

Datos inventados.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests.test_doc1_documentos import FACTURA, _respuesta
from tests.test_maria1a_lectura_factura import COPIAS, _leer
from tests.test_maria1b_devolucion import EXPORT
from tests.test_maria7_rechazos_24_10 import LONA, _registrar_con_cuit
from tests.test_valor1 import _pedido_con

FORMA = "Destinación: va un código de 4 letras o números"
RUTAS = ["/generate_maria", "/generate_maria/avisos"]


def _entrar(client):
    _registrar_con_cuit(client, f"avisos2_{uuid.uuid4().hex[:10]}")


def _ista(contenido):
    return [l for l in contenido.splitlines() if l.startswith(("ISTA=", "CDDTTYPDEC="))]


# ------------------------------------------------- 1. la forma del código


@pytest.mark.parametrize("destinacion, sale", [
    ("IC04", "IC04"), (" ic04 ", "IC04"), ("IC01", "IC01"), ("ZFI1", "ZFI1"), ("TRAN", "TRAN"), ("", "IC04"),
])
def test_una_destinacion_de_importacion_valida_sale_igual(client, destinacion, sale):
    _entrar(client)
    pedido = _pedido_con([LONA], tipo_destinacion=destinacion)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert _ista(r.json()["content"]) == [f"ISTA={sale}", f"CDDTTYPDEC={sale}"]
    assert client.post("/generate_maria/avisos", json=pedido).status_code == 200


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("destinacion", [
    "0EC01", "XEC01", "IC041", "IC0", "​IC04", "IC​04", "ᴇC01", "ＩＣ０４",
    "ıc04", "ICØ04", "IC-4", "IC_4",
])
def test_lo_que_no_es_un_codigo_da_400_y_no_genera(client, ruta, destinacion):
    _entrar(client)
    r = client.post(ruta, json=_pedido_con([LONA], tipo_destinacion=destinacion))
    assert r.status_code == 400, r.text
    assert r.json()["detail"].startswith(FORMA) and "IC04" in r.json()["detail"], r.text


@pytest.mark.parametrize("destinacion", ["IC041", "IC0", "IC-4", "ＩＣ０４"])
def test_el_generador_tampoco_escribe_lo_que_no_es_un_codigo(destinacion):
    from tests.test_generar_maria_txt import _gen
    with pytest.raises(ValueError, match=FORMA):
        _gen("SINT-FORMA", [], tipo_destinacion=destinacion)


# ------------------------------------------------- 2. la exportación


@pytest.mark.parametrize("destinacion, status", [
    ("EC01", 200), (" ec01 ", 200), ("EC05", 200),
    ("IC04", 400), ("TRAN", 400), ("ZFI1", 400), ("", 400), ("0EC01", 400), ("EC011", 400), ("​EC01", 400),
    pytest.param(" " * 70 + "EC01", 200, id="70blancos-EC01-200"),
])
def test_la_exportacion_sólo_genera_con_una_ec(destinacion, status):
    r = TestClient(main.app).post("/generate_maria_export", json={**EXPORT, "tipo_destinacion": destinacion})
    assert r.status_code == status, r.text[:300]
    if status == 200:
        codigo = destinacion.strip().upper()
        assert _ista(r.json()["content"]) == [f"ISTA={codigo}", f"CDDTTYPDEC={codigo}"]
    else:
        assert "EC01" in r.json()["detail"], r.text


# ------------------------------------------------- 3. un texto enorme


def test_un_texto_enorme_no_se_normaliza_entero(monkeypatch):
    from proyecto_maria.core import maria_generator
    largos = []
    original = maria_generator.unicodedata.normalize

    def espiar(forma, texto):
        largos.append(len(texto))
        return original(forma, texto)

    monkeypatch.setattr(maria_generator.unicodedata, "normalize", espiar)
    for texto in ("​" * 2_000_000 + "EC01", "IC04" + "A" * 2_000_000):
        with pytest.raises(ValueError):
            maria_generator.destinacion_del_txt(texto)
    assert largos and max(largos) <= 64, largos


# ------------------------------------------------- 4. el seguro borrado en FOB


def test_el_seguro_borrado_de_vuelta_a_fob_dice_lo_que_paso(client):
    _entrar(client)
    pedido = _pedido_con([LONA], incoterm="FOB", seguro="", seguro_para_completar=True, seguro_borrado=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert "se borró al cambiar el incoterm" in detalle and "en el precio" not in detalle, detalle
    assert detalle in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]


# ------------------------------------------------- 5. el lector de PDF


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("lugar, valor", [
    ("documento", "​EC01"), ("documento", "ㅤec02"), ("operacion", "​EC01"), ("raiz", "﻿EC03"),
    pytest.param("documento", " " * 70 + "EC01", id="documento-70blancos"),
    pytest.param("operacion", "\xa0" * 70 + "EC01", id="operacion-70nbsp"),
])
def test_el_lector_rechaza_la_exportacion_con_lo_invisible_adelante(monkeypatch, copia, lugar, valor):
    respuesta = _respuesta(dict(FACTURA, destinacion=valor) if lugar == "documento" else FACTURA)
    if lugar != "documento":
        (respuesta if lugar == "raiz" else respuesta["operacion"])["tipo_destinacion"] = valor
    with pytest.raises(ValueError, match="factura comercial de importación"):
        _leer(monkeypatch, copia, respuesta, clasificar=False)


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("valor, queda", [
    ("\u200b" * 65 + "EC01", ""), ("IC-04", ""), ("IC04 (consumo)", ""), ("\u200bIC04", ""),
    ("ＩＣ０４", ""), ("IC_4", ""), ("\u212aC04", ""), (" ic04 ", "IC04"),
])
def test_el_lector_deja_vacio_lo_que_no_es_un_codigo(monkeypatch, copia, valor, queda):
    r = _leer(monkeypatch, copia, _respuesta(dict(FACTURA, destinacion=valor)), clasificar=False)
    assert (r["documento"]["destinacion"], r["operacion"]["tipo_destinacion"]) == (queda, queda), r["documento"]


# ------------------------------------------------- 6. el default del perfil


@pytest.mark.parametrize("default, status, queda", [
    ("IC041", 400, "IC05"), ("IC0", 400, "IC05"), ("EC01", 400, "IC05"), ("IC_4", 400, "IC05"),
    (" ic04 ", 200, "IC04"), ("", 200, ""),
])
def test_el_perfil_solo_guarda_un_codigo_de_importacion(client, default, status, queda):
    _entrar(client)
    assert client.put("/api/user/profile", json={"default_tipo_destinacion": "IC05"}).status_code == 200
    r = client.put("/api/user/profile", json={"default_tipo_destinacion": default, "name": "Otro nombre"})
    assert r.status_code == status, r.text
    perfil = client.get("/api/user/profile").json()["profile"]
    assert perfil["default_tipo_destinacion"] == queda, perfil
    assert (perfil["name"] == "Otro nombre") == (status == 200), perfil
