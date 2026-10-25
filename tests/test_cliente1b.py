"""CLIENTE-1b: la fecha de inicio de actividad se valida en la API.

En el alta (POST) y en la edición (PUT): `null` y vacío dejan la fecha vacía;
pasan AAAA-MM-DD (año de cuatro cifras, fecha que existe) y DD/MM/AAAA, que
se guarda AAAA-MM-DD; lo demás es un error que nombra el campo y no guarda
nada. Todo con datos inventados."""
import uuid

import pytest

# (lo que manda la API, la fecha que tiene que quedar o None si es un error)
FAMILIA = [
    (None, ""),
    ("", ""),
    ("   ", ""),
    ("None", None),
    ("20150-01-01", None),
    ("2015-02-30", None),
    ("15/03/2015", "2015-03-15"),
    ("5/3/2015", "2015-03-05"),
    ("2015-03-15", "2015-03-15"),
    (" 2015-03-15 ", "2015-03-15"),
    ("15/03/15", None),
    ("31/04/2015", None),
    ("2015-03-15T00:00:00", None),
    ("mar-2015", None),
    (20150315, None),
    (True, None),
]
IDS = [repr(v) for v, _ in FAMILIA]


def _nombre():
    return f"Cliente Inventado 1b {uuid.uuid4().hex[:8]}"


def _fecha(client, cid):
    r = client.get(f"/api/clientes/{cid}")
    assert r.status_code == 200, r.text
    return r.json()["fecha_inic_activ"]


def _error_de_fecha(r):
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert "fecha de inicio de actividad" in detalle, detalle
    assert "AAAA-MM-DD" in detalle and "DD/MM/AAAA" in detalle, detalle


@pytest.mark.parametrize("enviada,queda", FAMILIA, ids=IDS)
def test_el_alta_valida_la_fecha_de_inicio(auth_override, client, enviada, queda):
    nombre = _nombre()
    r = client.post("/api/clientes", json={"nombre": nombre, "fecha_inic_activ": enviada})
    if queda is None:
        _error_de_fecha(r)
        lista = client.get("/api/clientes").json()
        lista = lista.get("clientes", lista) if isinstance(lista, dict) else lista
        assert not [c for c in lista if c["nombre"] == nombre], "con la fecha mala igual se creó"
        return
    assert r.status_code == 200, r.text
    assert r.json()["cliente"]["fecha_inic_activ"] == queda
    assert _fecha(client, r.json()["cliente"]["id"]) == queda


@pytest.mark.parametrize("enviada,queda", FAMILIA, ids=IDS)
def test_la_edicion_valida_la_fecha_de_inicio(auth_override, client, enviada, queda):
    r = client.post("/api/clientes", json={"nombre": _nombre(), "fecha_inic_activ": "2010-06-01"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    r = client.put(f"/api/clientes/{cid}", json={
        "direccion": "Calle Inventada 9", "fecha_inic_activ": enviada})
    if queda is None:
        _error_de_fecha(r)
        # Con la fecha mala no se guarda nada: ni la fecha ni el resto.
        datos = client.get(f"/api/clientes/{cid}").json()
        assert datos["fecha_inic_activ"] == "2010-06-01"
        assert datos["direccion"] == ""
        return
    assert r.status_code == 200, r.text
    assert r.json()["cliente"]["fecha_inic_activ"] == queda
    assert _fecha(client, cid) == queda


def test_editar_sin_mandar_la_fecha_la_conserva(auth_override, client):
    """D3: la pantalla no manda la fecha que no puede mostrar; la API no la toca."""
    r = client.post("/api/clientes", json={"nombre": _nombre(), "fecha_inic_activ": "2010-06-01"})
    cid = r.json()["cliente"]["id"]
    r = client.put(f"/api/clientes/{cid}", json={"direccion": "Calle Inventada 9"})
    assert r.status_code == 200, r.text
    assert _fecha(client, cid) == "2010-06-01"


def test_el_alta_sin_la_fecha_la_deja_vacia(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": _nombre()})
    assert r.status_code == 200, r.text
    assert r.json()["cliente"]["fecha_inic_activ"] == ""
