"""Un cuerpo muy hondo, un NUL en la consulta, un campo del cliente que no es
texto o un número enorme no dan 500 ni se guardan.

El log de pedidos y la suma de valores en Postgres están en
`scripts/testing/entradas3_postgres.py`.
"""
import pytest
from sqlalchemy import select

from proyecto_maria.database.models import ClientProductHistory
from tests.test_entradas1 import _post
from tests.test_entradas2 import _cliente, _cliente_guardado, _manual, _operaciones, _sesion
from tests.test_sesion1 import (  # noqa: F401  (las dos fixtures se usan solas)
    _consulta, _sin_limites, _tablas,
)

# Pasa el parseo del cuerpo (que corta recién hacia los 20000 niveles) y no la pila de Python.
HONDO = b"[" * 2000 + b"]" * 2000


def _productos(cid):
    async def _f(s):
        return (await s.execute(select(ClientProductHistory.id).where(ClientProductHistory.client_id == cid))).scalars().all()
    return _consulta(_f)


def _producto(sesion, cid):
    r = _post(f"/api/clientes/{cid}/catalogo/productos/learn",
              {"items": [{"ncm": "8471.30.12", "descripcion": "D"}]}, sesion)
    assert r.json().get("aprendidos") == 1, r.text
    return _productos(cid)[0]


# ruta (con {cid} y {pid}), método, cuerpo con algo más hondo que la pila
CUERPOS_HONDOS = {
    "aprender_productos": ("/api/clientes/{cid}/catalogo/productos/learn", "POST",
                           b'{"items": [{"descripcion": "D"}], "x": %s}' % HONDO),
    "guardar_despacho": ("/api/clientes/{cid}/catalogo/despacho/guardar", "POST",
                         b'{"renglones": [{"posicion_sim": "8471.30.12", "descripcion": "D", "x": %s}]}' % HONDO),
    "editar_producto": ("/api/clientes/{cid}/catalogo/productos/{pid}", "PUT", b'{"x": %s}' % HONDO),
}


@pytest.mark.parametrize("ruta,metodo,cuerpo", CUERPOS_HONDOS.values(), ids=list(CUERPOS_HONDOS))
def test_cuerpo_mas_hondo_que_la_pila_da_400(ruta, metodo, cuerpo):
    _, sesion = _sesion()
    cid = _cliente(sesion)
    pid = _producto(sesion, cid)
    r = _post(ruta.format(cid=cid, pid=pid), cuerpo, sesion, metodo=metodo)
    assert r.status_code == 400, r.text
    assert _productos(cid) == [pid]


def test_nul_en_la_consulta_da_400():
    _, sesion = _sesion()
    r = _post("/api/clientes/search?q=a%00b", b"", sesion, metodo="GET")
    assert r.status_code == 400, r.text


def _hondo(n):
    valor = {}
    for _ in range(n):
        valor = {"a": valor}
    return valor


NO_TEXTOS = {"lista": ["a"], "objeto": {"a": 1}, "numero": 3, "booleano": True, "objeto_hondo": _hondo(900)}
CAMPOS = ["nombre", "email", "telefono", "cuit", "direccion", "notas", "default_origin", "preferred_currency"]


@pytest.mark.parametrize("via", ["alta", "edicion"])
def test_campo_del_cliente_que_no_es_texto_da_400_y_no_guarda(via):
    _, sesion = _sesion()
    cid = _cliente(sesion)
    for campo in CAMPOS:
        for nombre, valor in NO_TEXTOS.items():
            cuerpo = {"nombre": "Nuevo", campo: valor}
            if via == "alta":
                r = _post("/api/clientes", cuerpo, sesion)
            else:
                r = _post(f"/api/clientes/{cid}", cuerpo, sesion, metodo="PUT")
            assert (r.status_code, r.json()["detail"]) == (400, f"{campo} tiene que ser texto."), (campo, nombre)
    listado = _post("/api/clientes", b"", sesion, metodo="GET").json()
    assert [c["nombre"] for c in listado["clientes"]] == ["C"]
    assert _cliente_guardado(cid).name == "C"


@pytest.mark.parametrize("via", ["alta", "edicion"])
def test_campo_del_cliente_en_null_queda_vacio(via):
    _, sesion = _sesion()
    cuerpo = {"nombre": "N", "email": None, "notas": None}
    if via == "alta":
        r = _post("/api/clientes", cuerpo, sesion)
    else:
        r = _post(f"/api/clientes/{_cliente(sesion, notas='x')}", cuerpo, sesion, metodo="PUT")
    assert r.status_code == 200, r.text
    guardado = _cliente_guardado(r.json()["cliente"]["id"])
    assert (guardado.email or "", guardado.notes or "") == ("", "")


ENORMES = ["1e308", "-1e308", "1e16"]


@pytest.mark.parametrize("numero", ENORMES)
def test_numero_enorme_da_400_y_no_guarda(numero):
    u, sesion = _sesion()
    cid = _cliente(sesion)
    for campo in ("cantidad", "valor_unitario", "peso_unitario"):
        item = '{"descripcion": "D", "cantidad": 1, "%s": %s}' % (campo, numero)
        r = _manual(sesion, cid, item)
        assert r.status_code == 400, (campo, r.text)
        assert "demasiado grande" in r.json()["detail"], campo
    for cuerpo in ('{"items": [{"descripcion": "D", "cantidad": %s}]}' % numero,
                   '{"items": [{"descripcion": "D", "valor_unitario": %s}]}' % numero,
                   '{"items": [], "resumen": {"valor_total": %s}}' % numero):
        r = _post(f"/api/clientes/{cid}/operaciones", cuerpo.encode(), sesion)
        assert r.status_code == 400, (cuerpo, r.text)
    assert _operaciones(u) == 0
