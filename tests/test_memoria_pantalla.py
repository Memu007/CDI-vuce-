"""La posición como la arma la pantalla alimenta la memoria del cliente por
cada entrada que la recibe: guardar-uso, la operación, learn y el PUT."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_guardar1 import _cliente
from tests.test_prelaunch_block2 import client  # noqa: F401

PANTALLA = Path(__file__).with_name("memoria_pantalla.js")
# Qué arma la pantalla: la posición individual, la de SIM+DC en lote, la de una
# sugerencia y la NCM de 8 dígitos.
PEDIDOS = {
    "individual": ["buildSimPosition", "84713000900", "r"],
    "lote": ["buildSimPosition", "8471.30.00.900", "R"],
    "sugerencia": ["formatNcm", "84713000900R"],
    "base": ["formatNcm", "84713000"],
}


@pytest.fixture(scope="module")
def posiciones():
    if not shutil.which("node"):
        pytest.skip("sin node")
    return json.loads(subprocess.run(
        ["node", str(PANTALLA), json.dumps(PEDIDOS)], capture_output=True, text=True, check=True, timeout=30,
    ).stdout)


@pytest.mark.parametrize("forma", sorted(PEDIDOS))
def test_pantalla_alimenta_memoria(client, posiciones, forma):
    posicion = posiciones[forma]
    cid = _cliente(client)
    base = f"/api/clientes/{cid}/catalogo/productos"

    r = client.post(f"{base}/learn", json={"items": [{"ncm": "84719000", "descripcion": "MONITOR PUT"}]})
    assert r.status_code == 200, r.text
    editado = client.get(base).json()["productos"][0]["id"]

    entradas = {
        "guardar-uso": client.post("/api/ncm/guardar-uso", json={
            "descripcion": "MONITOR GUARDAR USO", "ncm": posicion, "origen": "CN", "client_id": cid}),
        "operacion": client.post(f"/api/clientes/{cid}/operaciones", json={"items": [{
            "pieza": posicion, "ncm": posicion, "descripcion": "MONITOR OPERACION",
            "cantidad": 1, "valor_unitario": 10}]}),
        "learn": client.post(f"{base}/learn", json={"items": [{"ncm": posicion, "descripcion": "MONITOR LEARN"}]}),
        "put": client.put(f"{base}/{editado}", json={"ncm": posicion}),
    }
    catalogo = {p["descripcion"]: p["ncm"] for p in client.get(base).json()["productos"]}
    assert ({e: r.status_code for e, r in entradas.items()}, catalogo) == (
        dict.fromkeys(entradas, 200),
        dict.fromkeys(("MONITOR GUARDAR USO", "MONITOR OPERACION", "MONITOR LEARN", "MONITOR PUT"), "84713000"),
    ), posicion
