"""CLIENTE-1c: la fecha de inicio de actividad que llega por la operación o por
la importación pasa por la misma regla que el alta (`_fecha_inic_activ_de_api`).

D15 (b): la operación sólo copia a la ficha vacía una fecha que sirve, y la
guarda AAAA-MM-DD; si no sirve no se copia y la operación se guarda igual.
D16 (b): la importación deja vacía la fecha que no sirve y la vista previa lo
dice con la fila. Además la ficha dice si la fecha guardada le sirve al TXT,
con el mismo criterio que el generador. Todo con datos inventados."""
import asyncio
import io
import uuid

import pytest
from sqlalchemy import select

from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Client as ClientModel, SystemBackup


def _cuit(serial: int) -> str:
    """Un CUIT inventado con el verificador bien (como en test_migration_import)."""
    candidato = serial * 10
    pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    while True:
        base = f"30{candidato:08d}"[-10:]
        verificador = 11 - sum(int(d) * p for d, p in zip(base, pesos)) % 11
        verificador = 0 if verificador == 11 else verificador
        if verificador != 10:
            return f"{base}{verificador}"
        candidato += 1


def _serial() -> int:
    return 70000000 + uuid.uuid4().int % 9000000


def _crear(client, **campos):
    r = client.post("/api/clientes", json={
        "nombre": f"Cliente Inventado 1c {uuid.uuid4().hex[:8]}", **campos})
    assert r.status_code == 200, r.text
    return r.json()["cliente"]


def _guardada(cid):
    async def _leer():
        async with AsyncSessionLocal() as s:
            c = (await s.execute(select(ClientModel).where(ClientModel.id == cid))).scalars().first()
            return c.fecha_inic_activ, c.address
    return asyncio.run(_leer())


def _sembrar(cid, fecha):
    """Una fecha vieja, como las que quedaron antes de CLIENTE-1b: la API ya no
    la acepta, así que va directo a la base."""
    async def _escribir():
        async with AsyncSessionLocal() as s:
            c = (await s.execute(select(ClientModel).where(ClientModel.id == cid))).scalars().first()
            c.fecha_inic_activ = fecha
            await s.commit()
    asyncio.run(_escribir())


# --- D15: la operación ------------------------------------------------------

def _operacion(client, cid, fecha, domicilio="Calle Inventada 77"):
    r = client.post(f"/api/clientes/{cid}/operaciones", json={
        "source": "pdf_v2", "currency": "USD",
        "comprador_domicilio": domicilio, "comprador_fecha_inic_activ": fecha,
        "resumen": {"items": 1, "valor_total": 100},
        "items": [{"pieza": "P1", "ncm": "3926.90.90", "descripcion": "Pieza inventada",
                   "origen": "CN", "cantidad": 1, "valor_unitario": 100, "peso_unitario": 1}],
    })
    assert r.status_code == 200, r.text  # la operación se guarda igual


# (lo que trae la operación, lo que queda en la ficha vacía)
OPERACION = [
    ("20150-01-0", None),
    ("None", None),
    ("2015-02-30", None),
    ("15/03/15", None),
    ("mar-2015", None),
    ("２０１５-03-15", None),
    ("2015-03-15", "2015-03-15"),
    ("15/03/2015", "2015-03-15"),
]


@pytest.mark.parametrize("trae,queda", OPERACION, ids=[t for t, _ in OPERACION])
def test_la_operacion_solo_copia_una_fecha_que_sirve(auth_override, client, trae, queda):
    cid = _crear(client)["id"]
    _operacion(client, cid, trae)
    fecha, domicilio = _guardada(cid)
    assert (fecha or None) == queda
    # El resto del relleno sigue como estaba.
    assert domicilio == "Calle Inventada 77"


def test_la_operacion_no_pisa_la_fecha_que_ya_tiene(auth_override, client):
    cid = _crear(client, fecha_inic_activ="2010-06-01")["id"]
    _operacion(client, cid, "2015-03-15")
    assert _guardada(cid)[0] == "2010-06-01"


# --- D16: la importación ----------------------------------------------------

def _csv(filas):
    lineas = ["CUIT,RAZON SOCIAL,FECHA INICIO ACTIVIDADES"]
    lineas += [",".join(f) for f in filas]
    return ("\n".join(lineas) + "\n").encode("utf-8")


def _analizar(client, contenido):
    r = client.post("/api/migrations/analyze",
                    files={"file": ("clientes.csv", io.BytesIO(contenido), "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()


def _confirmar(client, batch_id):
    r = client.post(f"/api/migrations/{batch_id}/confirm")
    assert r.status_code == 200, r.text
    return r.json()


def _por_cuit(client, cuit):
    r = client.get(f"/api/clientes/by-cuit/{cuit}")
    assert r.status_code == 200, r.text
    return r.json()["cliente"]


def test_la_vista_previa_avisa_la_fila_con_la_fecha_que_no_sirve(auth_override, client):
    malo, bueno = _cuit(_serial()), _cuit(_serial())
    preview = _analizar(client, _csv([
        [malo, "Importadora Inventada Mala", "20150-01-0"],
        [bueno, "Importadora Inventada Buena", "01/06/2018"],
    ]))["preview"]
    avisos = preview["fechas_que_no_sirven"]
    assert [(a["row"], a["cuit"], a["value"]) for a in avisos] == [(2, malo, "20150-01-0")]
    assert preview["summary"]["fechas_que_no_sirven"] == 1
    # No vuelve conflicto al cliente: se importa sin la fecha.
    nuevos = {r["cuit"]: r for r in preview["new_clients"]}
    assert nuevos[malo]["ready"] is True and nuevos[malo]["fecha_inic_activ"] == ""
    assert nuevos[bueno]["fecha_inic_activ"] == "2018-06-01"
    assert not preview["conflicts"]


def test_con_el_cuit_repetido_la_fecha_que_sirve_es_la_que_queda(auth_override, client):
    """El aviso es de la fila, no del cliente: la fecha que no sirve no se usa
    y otra fila del mismo CUIT puede traer la buena."""
    cuit = _cuit(_serial())
    preview = _analizar(client, _csv([
        [cuit, "Importadora Inventada Repetida", "20150-01-0"],
        [cuit, "Importadora Inventada Repetida", "01/06/2018"],
    ]))["preview"]
    assert [(a["row"], a["value"]) for a in preview["fechas_que_no_sirven"]] == [(2, "20150-01-0")]
    assert [r["fecha_inic_activ"] for r in preview["new_clients"]] == ["2018-06-01"]


def test_sin_fechas_malas_no_hay_aviso(auth_override, client):
    preview = _analizar(client, _csv([[_cuit(_serial()), "Importadora Inventada", ""]]))["preview"]
    assert preview["fechas_que_no_sirven"] == []
    assert preview["summary"]["fechas_que_no_sirven"] == 0


def test_la_importacion_guarda_el_anio_con_cuatro_cifras(auth_override, client):
    """`strftime('%Y')` no rellena: el año 1 quedaba «1-02-01»."""
    cuit = _cuit(_serial())
    lote = _analizar(client, _csv([[cuit, "Importadora Inventada Antigua", "01/02/0001"]]))
    assert lote["preview"]["new_clients"][0]["fecha_inic_activ"] == "0001-02-01"
    assert _confirmar(client, lote["batch_id"])["created"] == 1
    assert _por_cuit(client, cuit)["fecha_inic_activ"] == "0001-02-01"


def _lote_con_fecha(client, cuit, fecha, nombre="Importadora Inventada Vieja"):
    """Un lote analizado y, después, con la fecha que dejaba la vista previa
    vieja: un lote que quedó sin confirmar cuando se publique esto."""
    lote = _analizar(client, _csv([[cuit, nombre, "01/06/2018"]]))

    async def _cambiar():
        async with AsyncSessionLocal() as s:
            b = (await s.execute(select(SystemBackup).where(SystemBackup.id == lote["batch_id"]))).scalars().first()
            datos = dict(b.data_json)
            preview = dict(datos["preview"])
            preview["staged_records"] = [dict(r, fecha_inic_activ=fecha) for r in preview["staged_records"]]
            datos["preview"] = preview
            b.data_json = datos
            await s.commit()
    asyncio.run(_cambiar())
    return lote["batch_id"]


@pytest.mark.parametrize("fecha", ["1-02-01", "20150-01-0", "2015-02-30"])
def test_la_confirmacion_no_crea_con_una_fecha_que_no_sirve(auth_override, client, fecha):
    cuit = _cuit(_serial())
    assert _confirmar(client, _lote_con_fecha(client, cuit, fecha))["created"] == 1
    assert _por_cuit(client, cuit)["fecha_inic_activ"] == ""


@pytest.mark.parametrize("fecha", ["1-02-01", "20150-01-0", "2015-02-30"])
def test_la_confirmacion_no_rellena_con_una_fecha_que_no_sirve(auth_override, client, fecha):
    cuit = _cuit(_serial())
    cid = _crear(client, cuit=cuit, direccion="")["id"]
    batch_id = _lote_con_fecha(client, cuit, fecha, nombre=_por_cuit(client, cuit)["nombre"])
    _confirmar(client, batch_id)
    assert (_guardada(cid)[0] or "") == ""


def test_la_confirmacion_rellena_con_la_fecha_que_sirve(auth_override, client):
    cuit = _cuit(_serial())
    cid = _crear(client, cuit=cuit)["id"]
    batch_id = _lote_con_fecha(client, cuit, "01/06/2018", nombre=_por_cuit(client, cuit)["nombre"])
    assert _confirmar(client, batch_id)["updated"] == 1
    assert _guardada(cid)[0] == "2018-06-01"


# --- La ficha dice si la fecha guardada le sirve al TXT ---------------------

# (guardada, sirve): el criterio es el del generador.
FICHA = [
    ("2015-03-15", True),
    ("15/03/2015", True),
    ("２０１５-03-15", True),   # el generador la lee: no es una falsa alarma
    ("２０１５-０３-15", False),
    ("20150-01-0", False),
    ("2015-02-30", False),
    ("None", False),
    ("", False),
]


@pytest.mark.parametrize("guardada,sirve", FICHA, ids=[g or "vacia" for g, _ in FICHA])
def test_la_ficha_dice_si_la_fecha_guardada_sirve(auth_override, client, guardada, sirve):
    cid = _crear(client)["id"]
    _sembrar(cid, guardada)
    r = client.get(f"/api/clientes/{cid}")
    assert r.status_code == 200, r.text
    assert r.json()["fecha_inic_activ_sirve"] is sirve
    lista = client.get("/api/clientes").json()
    lista = lista.get("clientes", lista) if isinstance(lista, dict) else lista
    assert [c["fecha_inic_activ_sirve"] for c in lista if c["id"] == cid] == [sirve]
