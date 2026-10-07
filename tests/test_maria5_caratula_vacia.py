"""MARIA-5, punto 3 (revisión de MARIA-1d): en el servidor, un campo de la
carátula que es entero «None», «null» o «N/A» (sin importar mayúsculas ni
espacios) cuenta como vacío. Sale el aviso de carátula y nunca llega al TXT ni
al nombre del archivo. Pasa con operaciones guardadas con el lector viejo.
"""
import re

import pytest

from tests.test_maria_subitems import ITEM_BASE, SUF_A

CAMPOS = ["vendedor_nombre", "vendedor_id", "comprador_nombre", "comprador_cuit",
          "comprador_domicilio", "moneda", "incoterm", "bl_numero", "buque_nombre",
          "contenedor_numero", "fecha_embarque"]


def _pedido(**campos):
    base = {"operation_id": "OP1", "items": [dict(ITEM_BASE, estado=2)],
            "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A,
            "vendedor_nombre": "Proveedor", "comprador_nombre": "Importadora",
            "comprador_cuit": "30999999990", "moneda": "DOL", "incoterm": "FOB"}
    return dict(base, **campos)


@pytest.mark.parametrize("vacio", ["None", "null", "N/A", " none ", "NULL", None])
def test_ningun_vacio_escrito_llega_al_txt(client, auth_override, vacio):
    pedido = _pedido(operation_id=vacio, **{c: vacio for c in CAMPOS})
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    data = r.json()
    for basura in ("None", "NON", "null", "N/A", "NUL"):
        assert not re.search(rf"={re.escape(basura)}\b", data["content"], re.I), basura
        assert basura.lower() not in data["filename"].lower()
    assert re.search(r"^IDSO=OP_\d+", data["content"], re.M), "sin número, el de la operación"
    avisos = " | ".join(data["supuestos"]).lower()
    for palabra in ("vendedor", "nombre del importador", "cuit del importador", "moneda", "incoterm"):
        assert palabra in avisos, palabra


@pytest.mark.parametrize("vacio", ["None", "n/a"])
def test_los_avisos_antes_de_generar_tambien(client, auth_override, vacio):
    pedido = _pedido(vendedor_nombre=vacio, comprador_cuit=vacio)
    avisos = " | ".join(client.post("/generate_maria/avisos", json=pedido).json()["avisos"]).lower()
    assert "vendedor" in avisos and "cuit del importador" in avisos


@pytest.mark.parametrize("valor", ["Nonetheless SA", "N/A Trading", "Null Corp"])
def test_un_nombre_que_contiene_la_palabra_queda(client, auth_override, valor):
    """La regla es por campo entero."""
    r = client.post("/generate_maria", json=_pedido(vendedor_nombre=valor))
    assert r.status_code == 200, r.text
    assert f"LDDTNOMFOD={valor}" in r.json()["content"]
