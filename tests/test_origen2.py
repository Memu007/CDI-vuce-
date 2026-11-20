"""El origen habitual del cliente acepta el nombre o el código del país, como el
catálogo: se guarda entero, y lo que no es un país da 400 sin guardar nada.

El largo lo hace cumplir Postgres, no SQLite: la migración y el caso del largo
están en `scripts/testing/origen2_postgres.py`.
"""
import pytest

from proyecto_maria.database.models import Client
from tests.test_entradas1 import _post
from tests.test_entradas2 import _cliente, _cliente_guardado, _sesion
from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    _consulta, _sin_limites, _tablas,
)

# lo escrito → lo que queda guardado
SE_GUARDAN = [
    ("BRASIL", "BRASIL"), ("Brasil", "Brasil"), ("Holanda", "Holanda"), ("países  bajos", "países bajos"),
    ("423 · PAISES BAJOS", "423 · PAISES BAJOS"),
    ("659 · ANTILLAS HOLANDESAS (TERRITORIO DE PAISES BAJOS)", "659 · ANTILLAS HOLANDESAS (TERRITORIO DE PAISES BAJOS)"),
    ("310", "310"), ("0434", "0434"), ("ARG", "ARG"), ("cn", "CN"), ("  br ", "BR"),
]
NO_SON_PAISES = ["Narnia", "tierra media", "CHI", "HOL", "XX", "<b>x</b>"]


def _clientes(sesion):
    return [c["nombre"] for c in _post("/api/clientes", b"", sesion, metodo="GET").json()["clientes"]]


def _guardar(via, sesion, cid, origen):
    cuerpo = {"nombre": "Nuevo", "default_origin": origen}
    if via == "alta":
        return _post("/api/clientes", cuerpo, sesion)
    return _post(f"/api/clientes/{cid}", cuerpo, sesion, metodo="PUT")


@pytest.mark.parametrize("via", ["alta", "edicion"])
def test_origen_habitual_es_un_pais_entero_o_da_400(via):
    _, sesion = _sesion()
    cid = _cliente(sesion, default_origin="CN")
    for escrito in NO_SON_PAISES:
        r = _guardar(via, sesion, cid, escrito)
        assert (r.status_code, r.json().get("detail")) == (
            400, f"No reconozco el origen «{escrito}»: usá el nombre o el código del país."), escrito
    assert _clientes(sesion) == ["C"]
    assert _cliente_guardado(cid).default_origin == "CN"
    # Sin origen, el alta toma el del modelo y la edición lo deja vacío.
    vacio = "CN" if via == "alta" else None
    for escrito, guardado in SE_GUARDAN + [("", vacio), (None, vacio)]:
        r = _guardar(via, sesion, cid, escrito)
        assert r.status_code == 200, (escrito, r.text)
        assert r.json()["cliente"]["default_origin"] == (guardado or ""), escrito
        assert _cliente_guardado(r.json()["cliente"]["id"]).default_origin == guardado, escrito


def test_editar_otro_dato_deja_el_origen_que_ya_estaba():
    _, sesion = _sesion()
    cid = _cliente(sesion)

    # Lo recortado a 3 antes de validar ya no se puede escribir por la API.
    async def _recortado(s):
        (await s.get(Client, cid)).default_origin = "CHI"
    _consulta(_recortado)
    r = _post(f"/api/clientes/{cid}", {"nombre": "Otro", "notas": "n"}, sesion, metodo="PUT")
    assert r.status_code == 200, r.text
    assert (_cliente_guardado(cid).name, _cliente_guardado(cid).default_origin) == ("Otro", "CHI")
