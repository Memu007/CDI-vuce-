"""DESPACHO-1a: bajar el catálogo de un cliente en Excel (2026-10-28).

- Un renglón por producto del historial del cliente (`ClientProductHistory`),
  en el mismo orden que la pantalla.
- Sólo los productos de ese cliente y de ese dueño; un cliente ajeno da el
  mismo 404 que el resto del catálogo.
- Las descripciones vienen de facturas de terceros: una celda que empieza con
  `=`, `+`, `-` o `@` queda como texto, nunca como fórmula.
- La posición sale como texto, con ceros y letra como está guardada.
Todo con datos inventados."""
import asyncio
import io
import uuid
from datetime import date, datetime, timezone

import pytest
from openpyxl import load_workbook

from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import ClientProductHistory

ENCABEZADOS = ["Posición", "Descripción", "Origen", "Valor unitario promedio",
               "Cantidad promedio", "Peso unitario promedio", "Veces usado", "Última vez"]


def _crear_cliente(client, nombre=None):
    r = client.post("/api/clientes", json={
        "nombre": nombre or f"Cliente Inventado D1a {uuid.uuid4().hex[:8]}"})
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _sembrar(cid, owner, **campos):
    """Un producto aprendido, directo a la base, como lo deja una MARIA guardada."""
    fila = {"ncm": "8471.30.12", "descripcion": "NOTEBOOK INVENTADA", "origen_frecuente": "CN",
            "valor_unitario_avg": 10.0, "cantidad_avg": 1.0, "peso_unitario_avg": 1.0,
            "veces_usado": 1, **campos}

    async def _escribir():
        async with AsyncSessionLocal() as s:
            s.add(ClientProductHistory(owner_username=owner, client_id=cid, **fila))
            await s.commit()
    asyncio.run(_escribir())


def _bajar(client, cid):
    return client.get(f"/api/clientes/{cid}/catalogo/productos.xlsx")


def _hoja(r):
    assert r.status_code == 200, r.text
    return load_workbook(io.BytesIO(r.content)).active


def _como_otro(auth_override):
    from proyecto_maria.main import app, get_current_user
    otro = dict(auth_override)
    otro["username"] = otro["effective_owner"] = f"otro_dueno_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: otro
    return otro


def _volver(auth_override):
    from proyecto_maria.main import app, get_current_user
    app.dependency_overrides[get_current_user] = lambda: auth_override


# --- Lo que se guardó es lo que se baja ------------------------------------

def test_el_archivo_se_abre_y_trae_lo_guardado(auth_override, client):
    cid = _crear_cliente(client)
    _sembrar(cid, "test_user", ncm="0101.21.00", descripcion="CABALLO INVENTADO", origen_frecuente="UY",
             valor_unitario_avg=1234.5, cantidad_avg=2.0, peso_unitario_avg=450.25, veces_usado=3,
             ultima_vez=datetime(2026, 10, 1, 15, 0, tzinfo=timezone.utc))
    _sembrar(cid, "test_user", ncm="8517130A", descripcion="TELEFONO INVENTADO", origen_frecuente="CN",
             valor_unitario_avg=99.99, cantidad_avg=10.0, peso_unitario_avg=0.2, veces_usado=7,
             ultima_vez=datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc))

    r = _bajar(client, cid)
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    hoja = _hoja(r)
    filas = list(hoja.iter_rows(values_only=True))
    assert list(filas[0]) == ENCABEZADOS
    # El mismo orden que la pantalla: el último usado primero.
    assert filas[1:] == [
        ("8517130A", "TELEFONO INVENTADO", "CN", 99.99, 10, 0.2, 7, datetime(2026, 10, 20)),
        ("0101.21.00", "CABALLO INVENTADO", "UY", 1234.5, 2, 450.25, 3, datetime(2026, 10, 1)),
    ]


def test_la_posicion_sale_como_texto_con_ceros_y_letra(auth_override, client):
    cid = _crear_cliente(client)
    for ncm in ("01012100", "0402100Z", "0101.21.00"):
        _sembrar(cid, "test_user", ncm=ncm)
    hoja = _hoja(_bajar(client, cid))
    celdas = [fila[0] for fila in hoja.iter_rows(min_row=2)]
    assert sorted(c.value for c in celdas) == ["0101.21.00", "01012100", "0402100Z"]
    assert all(c.data_type == "s" for c in celdas)
    assert all(c.number_format == "@" for c in celdas)


def test_un_catalogo_vacio_trae_solo_los_encabezados(auth_override, client):
    cid = _crear_cliente(client)
    hoja = _hoja(_bajar(client, cid))
    assert [list(f) for f in hoja.iter_rows(values_only=True)] == [ENCABEZADOS]


# --- Celdas que una planilla tomaría como fórmula --------------------------

@pytest.mark.parametrize("texto", [
    '=HYPERLINK("http://ejemplo.invalid","ver")',
    "+1+1",
    "-2+3",
    "@SUMA(A1)",
])
def test_una_descripcion_con_formula_queda_como_texto(auth_override, client, texto):
    cid = _crear_cliente(client)
    _sembrar(cid, "test_user", descripcion=texto, origen_frecuente="=1")
    hoja = _hoja(_bajar(client, cid))
    desc, origen = hoja.cell(row=2, column=2), hoja.cell(row=2, column=3)
    for celda, esperado in ((desc, texto), (origen, "=1")):
        assert celda.value == esperado
        assert celda.data_type == "s", celda.data_type
        # Si alguien la edita en Excel, sigue siendo texto.
        assert celda.quotePrefix is True


def test_una_descripcion_con_caracteres_de_control_no_rompe_la_descarga(auth_override, client):
    cid = _crear_cliente(client)
    _sembrar(cid, "test_user", descripcion="TORNILLO\x01INVENTADO\x0b")
    hoja = _hoja(_bajar(client, cid))
    assert hoja.cell(row=2, column=2).value == "TORNILLOINVENTADO"


def test_el_nombre_del_archivo_es_ascii(auth_override, client):
    cid = _crear_cliente(client, nombre=f"Ñandú Café — Inventado 🚢 {uuid.uuid4().hex[:6]}")
    r = _bajar(client, cid)
    assert r.status_code == 200, r.text
    disposicion = r.headers["content-disposition"]
    disposicion.encode("ascii")
    assert disposicion.startswith('attachment; filename="catalogo_')
    assert disposicion.endswith('.xlsx"')


# --- Aislamiento -----------------------------------------------------------

def test_otro_dueno_recibe_el_mismo_404_que_en_el_catalogo(auth_override, client):
    cid = _crear_cliente(client)
    _sembrar(cid, "test_user", descripcion="SECRETO INVENTADO")
    _como_otro(auth_override)
    try:
        r = _bajar(client, cid)
        r_pantalla = client.get(f"/api/clientes/{cid}/catalogo/productos")
    finally:
        _volver(auth_override)
    assert r.status_code == 404
    assert r.json() == r_pantalla.json() == {"detail": "Cliente no encontrado"}
    assert b"SECRETO" not in r.content


def test_un_cliente_que_no_existe_da_404(auth_override, client):
    r = _bajar(client, str(uuid.uuid4()))
    assert r.status_code == 404
    assert r.json() == {"detail": "Cliente no encontrado"}


def test_no_se_mezclan_los_productos_de_otro_cliente_ni_de_otro_dueno(auth_override, client):
    cid_a = _crear_cliente(client)
    cid_b = _crear_cliente(client)
    _sembrar(cid_a, "test_user", descripcion="DEL CLIENTE A")
    _sembrar(cid_b, "test_user", descripcion="DEL CLIENTE B")
    # Una fila con el cliente A pero de otro dueño: no es de este catálogo.
    _sembrar(cid_a, f"otro_dueno_{uuid.uuid4().hex[:8]}", descripcion="DE OTRO DUENO")

    def descripciones(cid):
        return [f[1] for f in _hoja(_bajar(client, cid)).iter_rows(min_row=2, values_only=True)]

    assert descripciones(cid_a) == ["DEL CLIENTE A"]
    assert descripciones(cid_b) == ["DEL CLIENTE B"]


def test_sin_sesion_da_401(client):
    r = client.get(f"/api/clientes/{uuid.uuid4()}/catalogo/productos.xlsx")
    assert r.status_code == 401
