"""CATALOGO-LARGO-1: una descripción de hasta 2000 caracteres se guarda en la
memoria del cliente y en el catálogo del proveedor, o da error a la vista.

Las tres memorias miden el tope en NFC, la forma en que guarda la memoria
del cliente: lo que entra en una entra en las otras. SQLite no controla el largo de las columnas: el corte de
Postgres lo prueba scripts/testing/catalogo_largo1_postgres.py.
"""
from urllib.parse import quote

import pytest

from tests.test_guardar1 import _cliente, _sql
from tests.test_prelaunch_block2 import client  # noqa: F401

VENDOR = "Proveedor sintetico"
VENDOR_ID = "proveedor_sintetico"
NCM = "73181500"
# U+0958 no se compone en NFC: 1001 caracteres crecen a 2002 al normalizar.
CRECE = "\u0958" * 1001
# e + acento agudo: 2002 caracteres que en NFC son 1001.
ACHICA = "e\u0301" * 1001

# (id, descripción, se guarda): igual en guardar-uso, el catálogo y el historial.
CASOS = [
    ("2000", "x" * 2000, True),
    ("nfd-que-achica", ACHICA, True),
    ("2001", "x" * 2001, False),
    ("nfc-que-crece", CRECE, False),
]
_casos = pytest.mark.parametrize("descripcion, guarda", [c[1:] for c in CASOS], ids=[c[0] for c in CASOS])


def _catalogo(owner):
    return _sql("select descripcion from vendor_catalog_products where owner_username=:o", o=owner)


def _dueno(cid):
    return _sql("select owner_username from clients where id=:c", c=cid)[0][0]


@_casos
def test_guardar_uso_guarda_en_las_dos_memorias_o_da_400(client, descripcion, guarda):
    cid = _cliente(client)
    owner = _dueno(cid)
    r = client.post("/api/ncm/guardar-uso", json={
        "descripcion": descripcion, "ncm": NCM, "client_id": cid, "vendor_name": VENDOR,
    })
    historial = _sql("select descripcion from client_product_history where client_id=:c", c=cid)
    if guarda:
        assert r.status_code == 200, r.text
        assert r.json() == {"success": True, "historial_guardado": True}
        assert len(historial) == 1 and len(_catalogo(owner)) == 1
    else:
        assert r.status_code == 400, r.text
        assert "2000" in r.json()["detail"]
        assert historial == [] and _catalogo(owner) == []
        assert _sql("select 1 from ncm_historial where owner_username=:o", o=owner) == []


@_casos
def test_guardar_en_el_catalogo_respeta_el_tope(client, descripcion, guarda):
    owner = _dueno(_cliente(client))
    r = client.post(f"/api/catalog/{VENDOR_ID}/productos", json={
        "vendor_name": VENDOR, "productos": [{"descripcion": "TORNILLO"}, {"descripcion": descripcion}],
    })
    if guarda:
        assert r.status_code == 200, r.text
        assert len(_catalogo(owner)) == 2
    else:
        assert r.status_code == 400, r.text
        assert "2000" in r.json()["detail"]
        assert _catalogo(owner) == []


@_casos
def test_importar_el_historial_respeta_el_tope(client, descripcion, guarda):
    owner = _dueno(_cliente(client))
    r = client.post("/api/ncm/import-historial", files={
        "file": ("h.csv", f"descripcion,ncm\n{descripcion},8413.70.10\n".encode("utf-8"), "text/csv")})
    historial = _sql("select descripcion from ncm_historial where owner_username=:o", o=owner)
    if guarda:
        assert r.status_code == 200, r.text
        assert historial == [(descripcion,)]
    else:
        assert r.status_code == 400 and "2000" in r.json()["detail"], r.text
        assert historial == []


def test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas(client):
    owner = _dueno(_cliente(client))
    largo = "a" * 1990
    r = client.post(f"/api/catalog/{VENDOR_ID}/productos", json={
        "vendor_name": VENDOR, "productos": [{"descripcion": largo}],
    })
    assert r.status_code == 200, r.text
    url = f"/api/catalog/{VENDOR_ID}/productos/{quote(largo)}"

    r = client.put(url, json={"descripcion_original": "b" * 2001})
    assert r.status_code == 400, r.text
    assert _catalogo(owner) == [(largo,)]

    r = client.put(url, json={"ncm": NCM})
    assert r.status_code == 200, r.text
    r = client.delete(url)
    assert r.status_code == 200 and r.json()["deleted"] is True, r.text
    assert _catalogo(owner) == []
