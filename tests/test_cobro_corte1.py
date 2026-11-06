"""Cuándo se cuenta una operación y dónde se corta el servicio.

- Una cuenta impaga, vencida o cancelada no genera ni gasta Gemini: 402 en las
  rutas que gastan Gemini o generan valor, con la razón real en el aviso.
- La operación es la fila que crea la primera generación; su `operacion_id`
  vuelve en la respuesta y se manda al regenerar y al guardar. Sin él, o con
  uno desconocido o ajeno, es una operación nueva y cuenta.
- El tope del plan se mira sólo donde se cuenta. Con el tope lleno se puede
  validar, volver a generar y bajar lo ya contado, y guardarlo en el cliente.
- Una operación admite 10 contenidos distintos; el 11.º es una operación nueva.

Cada caso usa su propia cuenta (registro y login, sin override) y datos
inventados. Las carreras van contra un Postgres local en
`scripts/testing/cobro_corte1_postgres.py`.
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from proyecto_maria import main
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Operation, Organization, User
from proyecto_maria.main import app
from tests.test_maria7_rechazos_24_10 import _pedido

CLAVE = "Clave-Segura-123"
ID_A = "FAC_CORTE1A"


def _correr(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def cuenta(monkeypatch):
    """Da (TestClient con sesión, username) de una cuenta nueva; con org=True,
    la cuenta es el admin de un estudio (la facturación es de la organización)."""
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    abiertos = []

    def _nueva(org=False):
        c = TestClient(app)
        abiertos.append(c)
        nombre = f"corte1_{uuid.uuid4().hex[:10]}"
        datos = {"username": nombre, "password": CLAVE, "email": f"{nombre}@cdi.test"}
        if org:
            r = c.post("/api/organizations/create", json={**datos, "name": f"Estudio {nombre}"})
        else:
            r = c.post("/auth/register", json={**datos, "name": nombre})
        assert r.status_code in (200, 201), r.text
        r = c.post("/auth/login", json={"username": nombre, "password": CLAVE})
        assert r.status_code == 200, r.text
        return c, nombre

    yield _nueva
    for c in abiertos:
        c.close()


def _fijar(username, de_la_org=False, **campos):
    """Pone campos de facturación en el usuario (o en su organización)."""
    async def _run():
        async with AsyncSessionLocal() as db:
            u = (await db.execute(select(User).where(User.username == username))).scalars().first()
            destino = u
            if de_la_org:
                destino = (await db.execute(
                    select(Organization).where(Organization.id == u.organization_id))).scalars().first()
            for k, v in campos.items():
                setattr(destino, k, v)
            await db.commit()
    _correr(_run())


def _leer(username, de_la_org=False):
    async def _run():
        async with AsyncSessionLocal() as db:
            u = (await db.execute(select(User).where(User.username == username))).scalars().first()
            fila = u
            if de_la_org:
                fila = (await db.execute(
                    select(Organization).where(Organization.id == u.organization_id))).scalars().first()
            return {"ops": fila.ops_used_this_period or 0, "extra": fila.extra_ops_remaining or 0,
                    "estado": fila.billing_status}
    return _correr(_run())


def _operaciones(username):
    async def _run():
        async with AsyncSessionLocal() as db:
            filas = (await db.execute(
                select(Operation).where(Operation.owner_username == username)
                .order_by(Operation.created_at))).scalars().all()
            return [{"id": o.id, "op_code": o.op_code, "archivo": o.generated_file, "creada": o.created_at,
                     "cliente": o.client_id, "source": o.source, "extra": dict(o.extra or {})}
                    for o in filas]
    return _correr(_run())


def _clientes(username):
    from proyecto_maria.database.models import Client

    async def _run():
        async with AsyncSessionLocal() as db:
            return len((await db.execute(
                select(Client).where(Client.owner_username == username))).scalars().all())
    return _correr(_run())


def _generar(c, operation_id=ID_A, flete=7925.0, operacion_id=""):
    pedido = _pedido()
    pedido.update(operation_id=operation_id, flete=flete, operacion_id=operacion_id)
    return c.post("/generate_maria", json=pedido)


def _oid(r):
    return r.json().get("operacion_id", "")


def _archivos(username):
    return sorted(os.listdir(main._user_downloads_dir(username)))


def _mismo_estudio(admin, otro):
    """Pone a `otro` en la organización de `admin`."""
    async def _run():
        async with AsyncSessionLocal() as db:
            org_id = (await db.execute(select(User.organization_id).where(User.username == admin))).scalar()
            u = (await db.execute(select(User).where(User.username == otro))).scalars().first()
            u.organization_id = org_id
            await db.commit()
    _correr(_run())


def _cliente(c, cuit="30999999995"):
    r = c.post("/api/clientes", json={"nombre": "Importadora Inventada", "cuit": cuit})
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _guardar(c, client_id, archivo="", operacion_id=""):
    return c.post(f"/api/clientes/{client_id}/operaciones", json={
        "operation_id": archivo, "operacion_id": operacion_id, "source": "maria",
        "resumen": {"items": 1, "valor_total": 1387.5}, "currency": "USD",
        "items": [{"pieza": "39219019900Z", "descripcion": "Lona de PVC gris 620 g",
                   "origen": "CN", "cantidad": 750, "valor_unitario": 1.85}],
    })


# ------------------------------------------------------------ espías de Gemini


@pytest.fixture
def gemini(monkeypatch):
    """Anota cada vez que una ruta llegaría a Gemini (PDF, NCM, migraciones)."""
    llamadas = []

    async def _leer_pdf(funcion, *args, **kw):
        llamadas.append("pdf")
        return {"items": [], "operacion": {}}

    def _ncm(descripcion, limit=5):
        llamadas.append("ncm")
        return []

    class _Mapeador:
        def __init__(self, *a, **kw):
            self.used = False

        async def __call__(self, headers, muestras):
            llamadas.append("migraciones")
            self.used = True
            return {}

    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(main, "_leer_pdf_aparte", _leer_pdf)
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "true")
    monkeypatch.setattr(main, "_suggest_ncm_with_gemini", _ncm)
    monkeypatch.setattr("proyecto_maria.services.migration_ai_mapper.GeminiMigrationHeaderMapper", _Mapeador)
    return llamadas


def _pdf():
    import io
    from pypdf import PdfWriter
    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


CSV_CON_ENCABEZADOS = b"nombre,cuit\nImportadora Inventada,30999999995\n"
# Encabezados que el análisis local no reconoce: los mandaría a Gemini.
CSV_SIN_ENCABEZADOS = b"razon,doc\nImportadora Inventada,30999999995\n"


def _lote(c):
    r = c.post("/api/migrations/analyze", files={"file": ("clientes.csv", CSV_CON_ENCABEZADOS, "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()["batch_id"]


# Cada ruta: (preparación con la cuenta al día, pedido).
RUTAS = {
    "generate_maria": (None, lambda c, _: _generar(c)),
    "generate_maria_export": (None, lambda c, _: c.post("/generate_maria_export", json={
        "operation_id": "EXP_CORTE1", "items": [{"ncm": "39219019", "descripcion": "Lona de PVC gris para toldos",
                                                 "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1,
                                                 "origen": "AR"}]})),
    "process_operation": (None, lambda c, _: c.post("/process_operation/", json={
        "operation_id": "OP_CORTE1", "items": [{"pieza": "39219019900Z", "descripcion": "Lona de PVC gris",
                                                "origen": "CN", "cantidad": 1, "valor_unitario": 10,
                                                "peso_unitario": 1}]})),
    "upload_pdf": (None, lambda c, _: c.post("/upload_pdf/public",
                                             files={"file": ("factura.pdf", _pdf(), "application/pdf")})),
    "ncm_sugerir": (None, lambda c, _: c.post("/api/ncm/sugerir",
                                              json={"descripcion": "lona de pvc para toldos"})),
    "migraciones_analizar": (None, lambda c, _: c.post("/api/migrations/analyze", files={
        "file": ("clientes.csv", CSV_SIN_ENCABEZADOS, "text/csv")})),
    "migraciones_confirmar": (_lote, lambda c, lote: c.post(f"/api/migrations/{lote}/confirm")),
}

AHORA = datetime.now(timezone.utc)
ESTADOS = {
    # (campos, code, frase del aviso, estado después)
    "impaga": ({"billing_status": "past_due", "payment_provider": "mercadopago",
                "payment_customer_id": "cus_inventado"},
               "SUBSCRIPTION_PAST_DUE", "pago pendiente", "past_due"),
    "prueba_vencida": ({"billing_status": "trial", "trial_ends_at": AHORA - timedelta(days=1)},
                       "TRIAL_EXPIRED", "Venció tu prueba gratis", "past_due"),
    # Sin Mercado Pago, en producción sólo vence una prueba.
    "suscripcion_vencida": ({"billing_status": "active", "trial_ends_at": AHORA - timedelta(days=10)},
                            "TRIAL_EXPIRED", "Venció tu prueba gratis", "past_due"),
    # La cancelada sigue hasta el fin del período; después, se corta.
    "cancelada": ({"billing_status": "canceled", "trial_ends_at": AHORA - timedelta(days=1)},
                  "TRIAL_EXPIRED", "Cancelaste tu suscripción", "canceled"),
}


@pytest.mark.parametrize("ruta", list(RUTAS))
@pytest.mark.parametrize("estado", list(ESTADOS))
def test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini(cuenta, gemini, estado, ruta):
    c, u = cuenta()
    campos, code, frase, despues = ESTADOS[estado]
    preparar, pedir = RUTAS[ruta]
    previo = preparar(c) if preparar else None
    _fijar(u, **campos)
    r = pedir(c, previo)
    # Primero Gemini: en rojo muestra que se gastó.
    assert gemini == [], (gemini, r.status_code)
    assert r.status_code == 402, (r.status_code, r.text[:300])
    detalle = r.json()["detail"]
    assert detalle["code"] == code, detalle
    assert frase in detalle["message"], detalle
    assert detalle["billing_status"] == despues, detalle
    assert _operaciones(u) == []
    assert _clientes(u) == 0
    assert _archivos(u) == []


@pytest.mark.parametrize("estado", list(ESTADOS))
def test_la_razon_del_402_es_la_misma_en_el_segundo_pedido(cuenta, estado):
    c, u = cuenta()
    _fijar(u, **ESTADOS[estado][0])
    primero, segundo = _generar(c), _generar(c)
    assert primero.status_code == segundo.status_code == 402, (primero.text, segundo.text)
    assert primero.json()["detail"] == segundo.json()["detail"]


def test_el_plan_legado_trial_genera_exporta_y_guarda(cuenta):
    c, u = cuenta()
    _fijar(u, plan="trial")
    r = _generar(c)
    assert r.status_code == 200, r.text
    e = _exportar(c)
    assert e.status_code == 200, e.text
    g = _guardar(c, _cliente(c), operacion_id=_oid(r))
    assert g.status_code == 200, g.text


def test_el_aviso_de_la_cuenta_sin_suscripcion_no_habla_del_tope(cuenta):
    c, u = cuenta()
    _fijar(u, billing_status="none")
    r = _generar(c)
    assert r.status_code == 402, r.text
    detalle = r.json()["detail"]
    assert detalle["code"] == "SUBSCRIPTION_INACTIVE", detalle
    assert "límite" not in detalle["message"], detalle


def test_la_suscripcion_dentro_de_la_gracia_genera(cuenta):
    c, u = cuenta()
    _fijar(u, billing_status="active", trial_ends_at=AHORA - timedelta(days=3))
    assert _generar(c).status_code == 200
    assert _leer(u)["estado"] == "active"


def test_la_cancelada_genera_hasta_el_fin_del_periodo(cuenta):
    """Cancelar no corta lo que ya se pagó."""
    c, u = cuenta()
    _fijar(u, billing_status="canceled", trial_ends_at=AHORA + timedelta(days=5))
    assert _generar(c).status_code == 200
    assert _leer(u)["estado"] == "canceled"


def test_la_organizacion_impaga_corta_a_su_miembro_aunque_el_usuario_diga_active(cuenta):
    c, u = cuenta(org=True)
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20))
    _fijar(u, de_la_org=True, billing_status="past_due", payment_provider="mercadopago")
    r = _generar(c)
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "SUBSCRIPTION_PAST_DUE"
    assert _operaciones(u) == []


def test_el_estudio_con_la_prueba_vencida_no_genera_ni_gasta_gemini(cuenta, gemini):
    # El trial vencido del usuario ya lo vence el login (get_current_user); el
    # del estudio sólo lo vence el corte.
    c, u = cuenta(org=True)
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20))
    _fijar(u, de_la_org=True, billing_status="trial", trial_ends_at=AHORA - timedelta(days=1))
    r = c.post("/api/ncm/sugerir", json={"descripcion": "lona de pvc para toldos"})
    assert gemini == [], (gemini, r.status_code)
    assert r.status_code == 402, r.text
    detalle = r.json()["detail"]
    assert detalle["code"] == "TRIAL_EXPIRED", detalle
    assert "Venció tu prueba gratis" in detalle["message"], detalle
    assert _leer(u, de_la_org=True)["estado"] == "past_due"


@pytest.mark.parametrize("ruta", ["importacion", "exportacion"])
@pytest.mark.parametrize("estado", list(ESTADOS))
def test_regenerar_lo_ya_contado_con_la_cuenta_que_no_esta_al_dia_da_402(cuenta, estado, ruta):
    # Lo ya contado no pasa por el tope, pero sí por el estado.
    generar = _generar if ruta == "importacion" else _exportar
    c, u = cuenta()
    oid = _oid(generar(c))
    campos, code, _, _ = ESTADOS[estado]
    _fijar(u, **campos)
    r = generar(c, flete=8000.0, operacion_id=oid)
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == code
    assert len(_operaciones(u)[0]["extra"]["maria_hashes"]) == 1


@pytest.mark.parametrize("estado", list(ESTADOS))
def test_guardar_lo_ya_generado_con_la_cuenta_que_no_esta_al_dia_da_402(cuenta, estado):
    c, u = cuenta()
    r = _generar(c)
    cid = _cliente(c)
    campos, code, _, _ = ESTADOS[estado]
    _fijar(u, **campos)
    r = _guardar(c, cid, r.json()["filename"], _oid(r))
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == code
    assert _operaciones(u)[0]["cliente"] is None


# ------------------------------------------------------------ cuándo se cuenta


def test_generar_cuenta_una_vez_por_operacion_y_la_crea(cuenta):
    c, u = cuenta()
    r = _generar(c)
    assert r.status_code == 200, r.text
    oid = _oid(r)
    assert r.json()["filename"] == f"MARIA_{ID_A}_{oid[-8:]}.TXT"
    assert _leer(u)["ops"] == 1
    ops = _operaciones(u)
    assert len(ops) == 1, ops
    assert ops[0]["id"] == oid and ops[0]["op_code"] == "OP-000001", ops
    assert ops[0]["archivo"] == r.json()["filename"], ops
    assert ops[0]["source"] == "maria" and ops[0]["cliente"] is None, ops

    # Regenerarla no cuenta ni crea otra.
    assert _oid(_generar(c, operacion_id=oid)) == oid
    assert _leer(u)["ops"] == 1
    assert len(_operaciones(u)) == 1

    # Otro id es otra operación, con el código siguiente.
    assert _generar(c, operation_id="FAC_CORTE1B").status_code == 200
    assert _leer(u)["ops"] == 2
    assert [o["op_code"] for o in _operaciones(u)] == ["OP-000001", "OP-000002"]


# (primer id, segundo id, el segundo lo genera otro miembro del estudio)
DOS_OPERACIONES = {
    "mismo_numero_de_dos_proveedores": ("FAC_0001", "FAC_0001", False),
    "ids_que_el_saneo_junta": ("A-1/2", "A-12", False),
    "sin_numero_de_factura": ("", "", False),
    "dos_miembros_del_estudio": ("FAC_0001", "FAC_0001", True),
}


@pytest.mark.parametrize("caso", list(DOS_OPERACIONES))
def test_dos_operaciones_nunca_comparten_una_fila(cuenta, caso):
    primero, segundo, otro_miembro = DOS_OPERACIONES[caso]
    c, u = cuenta(org=True)
    r1 = _generar(c, operation_id=primero)
    assert r1.status_code == 200, r1.text
    c2, u2 = c, u
    if otro_miembro:
        c2, u2 = cuenta()
        _mismo_estudio(u, u2)
    # El otro miembro manda el operacion_id del primero: para él es ajeno.
    r2 = _generar(c2, operation_id=segundo, flete=8000.0,
                  operacion_id=_oid(r1) if otro_miembro else "")
    assert r2.status_code == 200, r2.text
    assert _leer(u, de_la_org=True)["ops"] == 2
    assert len(_operaciones(u)) + (len(_operaciones(u2)) if otro_miembro else 0) == 2
    assert c.get(r1.json()["download_url"]).text == r1.json()["content"]
    assert _oid(r1) != _oid(r2)


def test_el_mismo_resultado_no_gasta_una_de_las_10(cuenta, monkeypatch):
    from proyecto_maria.core import maria_generator_export

    c, u = cuenta()
    oid = _oid(_generar(c))
    assert _oid(_generar(c, operacion_id=oid)) == oid
    hoy = _exportar(c)
    assert hoy.status_code == 200, hoy.text

    class _Manana(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz) + timedelta(days=1)

    monkeypatch.setattr(maria_generator_export, "datetime", _Manana)
    manana = _exportar(c, operacion_id=_oid(hoy))
    assert manana.status_code == 200, manana.text
    assert manana.json()["content"] != hoy.json()["content"], "la fecha no cambió el archivo"
    assert [len(o["extra"]["maria_hashes"]) for o in _operaciones(u)] == [1, 1]
    assert _leer(u)["ops"] == 2


def test_otra_fecha_de_factura_en_la_importacion_gasta_una_de_las_10(cuenta):
    c, u = cuenta()
    oid = _oid(_generar(c))
    pedido = _pedido()
    pedido.update(operation_id=ID_A, operacion_id=oid, fecha_emision="01/01/2026")
    otra = c.post("/generate_maria", json=pedido)
    assert otra.status_code == 200, otra.text
    assert _oid(otra) == oid
    assert len(_operaciones(u)[0]["extra"]["maria_hashes"]) == 2
    assert _leer(u)["ops"] == 1


def test_borrar_el_cliente_no_recuenta_lo_generado(cuenta):
    c, u = cuenta()
    r = _generar(c)
    oid = _oid(r)
    cid = _cliente(c)
    assert _guardar(c, cid, r.json()["filename"], oid).status_code == 200
    assert c.delete(f"/api/clientes/{cid}").status_code == 200
    assert _generar(c, operacion_id=oid).status_code == 200
    assert _generar(c, flete=8000.0, operacion_id=oid).status_code == 200
    assert _leer(u)["ops"] == 1
    ops = _operaciones(u)
    assert [(o["id"], o["cliente"]) for o in ops] == [(oid, None)], ops
    assert len(ops[0]["extra"]["maria_hashes"]) == 2


def test_la_11_distinta_es_una_operacion_nueva_contada(cuenta):
    assert main.MARIA_REGENERACIONES == 10
    c, u = cuenta()
    r = _generar(c, flete=7925.0)
    oid = _oid(r)
    for i in range(1, 10):
        assert _oid(_generar(c, flete=7925.0 + i, operacion_id=oid)) == oid, i
    decimo = c.get(r.json()["download_url"]).text
    assert _leer(u)["ops"] == 1

    once = _generar(c, flete=9999.0, operacion_id=oid)
    assert once.status_code == 200, once.text
    assert _oid(once) not in ("", oid)
    assert once.json()["filename"] != r.json()["filename"]
    assert _leer(u)["ops"] == 2
    assert c.get(r.json()["download_url"]).text == decimo
    assert len(_operaciones(u)[0]["extra"]["maria_hashes"]) == 10

    # Un contenido que ya se generó sigue saliendo de la primera, sin contar.
    assert _oid(_generar(c, flete=7925.0 + 3, operacion_id=oid)) == oid
    assert _leer(u)["ops"] == 2


@pytest.mark.parametrize("org", [False, True])
def test_el_periodo_nuevo_no_hereda_las_regeneraciones(cuenta, org):
    c, u = cuenta(org=org)
    oid = _oid(_generar(c))
    _fijar(u, de_la_org=org, billing_period_started_at=datetime.now(timezone.utc) + timedelta(minutes=1))
    assert _oid(_generar(c, operacion_id=oid)) == oid
    assert _leer(u, de_la_org=org)["ops"] == 1
    nueva = _generar(c, flete=8000.0, operacion_id=oid)
    assert nueva.status_code == 200, nueva.text
    assert _oid(nueva) not in ("", oid)
    assert _leer(u, de_la_org=org)["ops"] == 2
    assert len(_operaciones(u)[0]["extra"]["maria_hashes"]) == 1


def test_la_operacion_del_mismo_segundo_es_del_periodo(cuenta):
    c, u = cuenta()
    oid = _oid(_generar(c))
    _fijar(u, billing_period_started_at=_operaciones(u)[0]["creada"].replace(microsecond=999999))
    assert _oid(_generar(c, flete=8000.0, operacion_id=oid)) == oid
    assert _leer(u)["ops"] == 1


def test_dos_operaciones_manuales_no_comparten_el_archivo(cuenta):
    c, u = cuenta()
    cid = _cliente(c)
    item = {"descripcion": "Lona de PVC gris", "cantidad": 750, "valor_unitario": 1.85}
    manuales = [c.post("/api/operations/manual", json={"client_id": cid, "items": [item]}) for _ in range(2)]
    assert all(m.status_code == 200 for m in manuales), [m.text for m in manuales]
    ids = [o["id"] for o in _operaciones(u)]
    assert len(ids) == 2 and all(i.startswith("MANUAL_") for i in ids), ids
    archivos = [_generar(c, operacion_id=i).json()["filename"] for i in ids]
    assert archivos[0] != archivos[1], archivos
    assert _leer(u)["ops"] == 2


def test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado(cuenta):
    c, u = cuenta()
    r = _generar(c)
    oid = _oid(r)
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20),
           ops_used_this_period=15, extra_ops_remaining=0)

    assert c.post("/generate_maria/avisos", json=_pedido()).status_code == 200
    assert c.post("/api/validate/smart", json={"items": [
        {"descripcion": "Lona de PVC", "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}]}
    ).status_code == 200
    assert c.get(r.json()["download_url"]).status_code == 200
    # Volver a generar la operación ya contada, igual o corregida, sale.
    assert _generar(c, operacion_id=oid).status_code == 200
    assert _generar(c, flete=8000.0, operacion_id=oid).status_code == 200
    # Guardarla en el cliente también.
    g = _guardar(c, _cliente(c), r.json()["filename"], oid)
    assert g.status_code == 200, g.text
    assert _leer(u)["ops"] == 15

    # Una operación nueva, no.
    r = _generar(c, operation_id="FAC_CORTE1NUEVA")
    assert r.status_code == 402, r.text
    detalle = r.json()["detail"]
    assert detalle["code"] == "PLAN_LIMIT_EXCEEDED", detalle
    assert "límite de 15" in detalle["message"], detalle
    assert len(_archivos(u)) == 1
    assert len(_operaciones(u)) == 1


def test_con_el_tope_lleno_el_extra_paga_la_operacion_nueva(cuenta):
    c, u = cuenta()
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20),
           ops_used_this_period=15, extra_ops_remaining=2,
           extra_ops_expires_at=AHORA + timedelta(days=20))
    assert _generar(c).status_code == 200
    assert _leer(u) == {"ops": 16, "extra": 1, "estado": "active"}


def test_la_organizacion_es_la_que_cuenta(cuenta):
    c, u = cuenta(org=True)
    assert _generar(c).status_code == 200
    assert _leer(u, de_la_org=True)["ops"] == 1
    assert _leer(u)["ops"] == 0


def test_sin_sesion_las_rutas_que_cuentan_dan_401(cuenta):
    from fastapi import HTTPException

    c, u = cuenta()
    cid = _cliente(c)
    antes = (_archivos("testing-user"), len(_operaciones("testing-user")))
    with TestClient(app) as anonimo:
        pedidos = {
            "generate_maria": lambda: _generar(anonimo),
            "generate_maria_export": lambda: _exportar(anonimo),
            "operations_manual": lambda: anonimo.post("/api/operations/manual", json={
                "client_id": cid, "items": [{"descripcion": "Lona", "cantidad": 1, "valor_unitario": 1}]}),
            "guardar": lambda: _guardar(anonimo, cid),
        }
        codigos = {ruta: pedir().status_code for ruta, pedir in pedidos.items()}
    assert codigos == dict.fromkeys(pedidos, 401), codigos
    assert (_archivos("testing-user"), len(_operaciones("testing-user"))) == antes

    # Con sesión de un usuario que no está en la base, cada paso que cuenta da 401.
    nadie = {"username": f"nadie_{uuid.uuid4().hex[:8]}"}
    pasos = {
        "require_billing_vigente": lambda db: main.require_billing_vigente(user=nadie, db=db),
        "require_active_billing": lambda db: main.require_active_billing(None, user=nadie, db=db),
        "_contar_operacion_bloqueada": lambda db: main._contar_operacion_bloqueada(db, nadie["username"]),
        "_contar_maria": lambda db: main._contar_maria(db, nadie["username"], "", "X", "X", 1, "MARIA_X"),
    }

    async def _codigo(paso):
        async with AsyncSessionLocal() as db:
            try:
                await paso(db)
            except HTTPException as e:
                return e.status_code
            return None

    assert {k: _correr(_codigo(p)) for k, p in pasos.items()} == dict.fromkeys(pasos, 401)
    assert _operaciones(u) == []


# ------------------------------------------------------------ guardar después


def test_guardar_despues_de_generar_no_cuenta_dos_veces(cuenta):
    c, u = cuenta()
    r = _generar(c)
    oid = _oid(r)
    cid = _cliente(c)
    g = _guardar(c, cid, r.json()["filename"], oid)
    assert g.status_code == 200, g.text
    ops = _operaciones(u)
    assert len(ops) == 1, ops
    assert g.json()["operation_id"] == ops[0]["id"] == oid
    assert g.json()["op_code"] == ops[0]["op_code"] == "OP-000001"
    assert ops[0]["cliente"] == cid and ops[0]["archivo"] == r.json()["filename"]
    assert ops[0]["extra"]["resumen"]["valor_total"] == 1387.5
    assert len(ops[0]["extra"]["maria_hashes"]) == 1
    assert _leer(u)["ops"] == 1

    # Volver a generar después de guardar tampoco cuenta.
    assert _oid(_generar(c, operacion_id=oid)) == oid
    assert _leer(u)["ops"] == 1


@pytest.mark.parametrize("operacion_id", ["", "desconocido"])
def test_guardar_sin_una_operacion_generada_cuenta_cada_vez(cuenta, operacion_id):
    c, u = cuenta()
    cid = _cliente(c)
    oid = operacion_id and str(uuid.uuid4())
    for _ in range(2):
        r = _guardar(c, cid, "MARIA_FAC_NUNCA.TXT", oid)
        assert r.status_code == 200, r.text
    assert [o["archivo"] for o in _operaciones(u)] == [None, None]
    assert _leer(u)["ops"] == 2


IDS_QUE_NO_SE_GUARDAN = {"nul": "a\x00b", "surrogate": "a\ud800b"}
ENVIAR_ID = {
    "generar": lambda c, oid: _generar(c, operacion_id=oid),
    "exportar": lambda c, oid: _exportar(c, operacion_id=oid),
    "guardar": lambda c, oid: _guardar(c, _cliente(c), "MARIA_FAC_RARO.TXT", oid),
}


@pytest.mark.parametrize("ruta", list(ENVIAR_ID))
@pytest.mark.parametrize("oid", list(IDS_QUE_NO_SE_GUARDAN))
def test_un_id_que_la_base_no_guarda_es_una_operacion_nueva(cuenta, ruta, oid):
    c, u = cuenta()
    r = ENVIAR_ID[ruta](c, IDS_QUE_NO_SE_GUARDAN[oid])
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 1 and len(_operaciones(u)) == 1


def test_guardar_con_la_operacion_de_otra_cuenta_no_la_toca(cuenta):
    a, ua = cuenta()
    b, ub = cuenta()
    r = _generar(a)
    g = _guardar(b, _cliente(b), r.json()["filename"], _oid(r))
    assert g.status_code == 200, g.text
    assert _leer(ub)["ops"] == 1
    ops_a = _operaciones(ua)
    assert len(ops_a) == 1 and ops_a[0]["cliente"] is None, ops_a
    assert _operaciones(ub)[0]["id"] != ops_a[0]["id"]


def test_guardar_en_otro_cliente_mueve_la_operacion(cuenta):
    c, u = cuenta()
    r = _generar(c)
    oid = _oid(r)
    a, b = _cliente(c), _cliente(c, cuit="30711111111")
    assert _guardar(c, a, r.json()["filename"], oid).status_code == 200
    assert _generar(c, flete=8000.0, operacion_id=oid).status_code == 200
    for _ in range(2):
        g = _guardar(c, b, r.json()["filename"], oid)
        assert g.status_code == 200, g.text
    assert _leer(u)["ops"] == 1
    ops = _operaciones(u)
    assert [(o["id"], o["cliente"]) for o in ops] == [(oid, b)], ops


def test_guardar_una_operacion_nueva_con_el_tope_lleno_da_402(cuenta):
    c, u = cuenta()
    cid = _cliente(c)
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20),
           ops_used_this_period=15, extra_ops_remaining=0)
    r = _guardar(c, cid, "MARIA_FAC_NUNCA.TXT")
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "PLAN_LIMIT_EXCEEDED"
    assert _operaciones(u) == []


def _items(operation_id):
    from proyecto_maria.database.models import OperationItem

    async def _run():
        async with AsyncSessionLocal() as db:
            return len((await db.execute(
                select(OperationItem).where(OperationItem.operation_id == operation_id))).scalars().all())
    return _correr(_run())


def test_guardar_dos_veces_lo_generado_reemplaza_los_items(cuenta):
    c, u = cuenta()
    r = _generar(c)
    cid = _cliente(c)
    for _ in range(2):
        assert _guardar(c, cid, r.json()["filename"], _oid(r)).status_code == 200
    ops = _operaciones(u)
    assert len(ops) == 1 and _items(ops[0]["id"]) == 1
    assert _leer(u)["ops"] == 1


def test_el_conteo_vence_la_cuenta_que_vencio_despues_del_corte(cuenta):
    # Toda ruta que cuenta pasa antes por el corte, que ya vence la cuenta en
    # otra transacción: si vence entre el corte y el conteo, el conteo la mira
    # de nuevo con la fila bloqueada. Se llama directo porque por la ruta ese
    # instante no se puede fijar.
    from fastapi import HTTPException

    _, u = cuenta(org=True)
    _fijar(u, de_la_org=True, billing_status="trial", trial_ends_at=AHORA - timedelta(days=1))

    async def _contar():
        async with AsyncSessionLocal() as db:
            await main._contar_operacion_bloqueada(db, u)
            await db.commit()

    with pytest.raises(HTTPException) as e:
        _correr(_contar())
    assert e.value.status_code == 402
    assert e.value.detail["code"] == "TRIAL_EXPIRED", e.value.detail
    assert _leer(u, de_la_org=True) == {"ops": 0, "extra": 0, "estado": "past_due"}


# ------------------------------------------------------------ exportación


def _exportar(c, operation_id="FAC_CORTE1EXP", flete=100.0, operacion_id=""):
    from tests.test_maria1b_devolucion import EXPORT
    return c.post("/generate_maria_export", json={**EXPORT, "operation_id": operation_id,
                                                  "flete": flete, "operacion_id": operacion_id})


def test_la_exportacion_cuenta_una_vez_por_operacion(cuenta):
    c, u = cuenta()
    r = _exportar(c)
    assert r.status_code == 200, r.text
    oid = _oid(r)
    assert _leer(u)["ops"] == 1, "la exportación no cuenta la operación"
    assert _exportar(c, operacion_id=oid).status_code == 200
    assert _exportar(c, flete=200.0, operacion_id=oid).status_code == 200
    assert _leer(u)["ops"] == 1, "volver a exportar la misma operación cuenta otra vez"
    ops = _operaciones(u)
    assert [o["archivo"] for o in ops] == [r.json()["filename"]], ops
    assert len(ops[0]["extra"]["maria_hashes"]) == 2, ops


def test_con_el_tope_lleno_la_exportacion_nueva_da_402_y_la_ya_contada_sale(cuenta):
    c, u = cuenta()
    oid = _oid(_exportar(c))
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20),
           ops_used_this_period=15, extra_ops_remaining=0)
    assert _exportar(c, flete=300.0, operacion_id=oid).status_code == 200
    r = _exportar(c, operation_id="FAC_CORTE1EXPNUEVA")
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "PLAN_LIMIT_EXCEEDED", r.json()
    assert len(_archivos(u)) == 1
    assert _leer(u)["ops"] == 15
    assert len(_operaciones(u)) == 1


@pytest.mark.parametrize("largo", [43, 44, 50, 60])
def test_la_exportacion_con_un_id_largo_cuenta_una_vez(cuenta, largo):
    c, u = cuenta()
    operation_id = ("FAC" + "9" * largo)[:largo]
    r = _exportar(c, operation_id=operation_id)
    assert r.status_code == 200, r.text
    oid = _oid(r)
    assert _exportar(c, operation_id=operation_id, flete=200.0, operacion_id=oid).status_code == 200
    assert _leer(u)["ops"] == 1, "volver a exportar el mismo id largo cuenta otra vez"
    assert _guardar(c, _cliente(c), r.json()["filename"], oid).status_code == 200
    assert _leer(u)["ops"] == 1, "guardar la exportación de id largo cuenta otra vez"
    assert len(_operaciones(u)) == 1


def test_una_importacion_con_id_export_no_reusa_la_exportacion(cuenta):
    # La importación «EXPORT_<x>» y la exportación «<x>» no comparten archivo.
    c, u = cuenta()
    assert _exportar(c, operation_id="FAC_CORTE1X").status_code == 200
    r = _generar(c, operation_id="EXPORT_FAC_CORTE1X")
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 2, "la importación reusó la operación de la exportación"
    assert len({o["archivo"] for o in _operaciones(u)}) == 2, _operaciones(u)


def _escritura_que_falla(ruta, mode="r", *a, **k):
    """Escribe una parte y se queda sin disco: el archivo queda creado."""
    f = open(ruta, mode, *a, **k)
    if "w" in mode:
        f.write("MARIA a medias")
        f.close()
        raise OSError("disco lleno")
    return f


def _supuestos_que_fallan(*a, **k):
    raise RuntimeError("falla después de contar")


async def _commit_que_falla(self):
    raise RuntimeError("la base se cayó al confirmar")


async def _rollback_que_falla(self):
    raise RuntimeError("la base se cayó al deshacer")


# (ruta, objeto y nombre que falla después de contar, su reemplazo)
LO_QUE_FALLA = {
    "importacion_al_escribir": ("importacion", main, "open", _escritura_que_falla),
    "importacion_despues_de_contar": ("importacion", main, "_supuestos_maria", _supuestos_que_fallan),
    "importacion_al_confirmar": ("importacion", main.AsyncSession, "commit", _commit_que_falla),
    "exportacion_al_escribir": ("exportacion", main, "open", _escritura_que_falla),
}


@pytest.mark.parametrize("caso", list(LO_QUE_FALLA))
def test_lo_no_entregado_no_queda_cobrado(cuenta, monkeypatch, caso):
    ruta, objeto, nombre, reemplazo = LO_QUE_FALLA[caso]
    pedir = _generar if ruta == "importacion" else _exportar
    c, u = cuenta()
    with monkeypatch.context() as m:
        m.setattr(objeto, nombre, reemplazo, raising=False)
        r = pedir(c)
    assert r.status_code == 500, r.text
    assert _leer(u)["ops"] == 0, "lo que no se entregó quedó contado"
    assert _operaciones(u) == [] and _archivos(u) == []

    r = pedir(c)
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 1 and len(_operaciones(u)) == 1
    assert _archivos(u) == [r.json()["filename"]]


# dónde falla regenerar lo ya entregado: (objeto, nombre, reemplazo)…, y si quedó
# el .anterior de un proceso cortado
AL_REGENERAR = {
    "al_escribir": ([(main, "open", _escritura_que_falla)], False),
    "al_confirmar": ([(main.AsyncSession, "commit", _commit_que_falla)], False),
    "al_confirmar_y_deshacer": ([(main.AsyncSession, "commit", _commit_que_falla),
                                 (main.AsyncSession, "rollback", _rollback_que_falla)], False),
    "al_escribir_con_un_anterior_viejo": ([(main, "open", _escritura_que_falla)], True),
}


@pytest.mark.parametrize("caso", list(AL_REGENERAR))
def test_regenerar_con_una_falla_deja_entero_lo_ya_entregado(cuenta, monkeypatch, caso):
    fallas, anterior_viejo = AL_REGENERAR[caso]
    c, u = cuenta()
    r = _generar(c)
    assert r.status_code == 200, r.text
    oid, archivo = _oid(r), r.json()["filename"]
    ruta = os.path.join(main._user_downloads_dir(u), archivo)
    entregado, antes = open(ruta, "rb").read(), _operaciones(u)
    if anterior_viejo:
        with open(ruta + ".anterior", "wb") as f:
            f.write(b"una version vieja")
    with monkeypatch.context() as m:
        for objeto, nombre, reemplazo in fallas:
            m.setattr(objeto, nombre, reemplazo, raising=False)
        r = _generar(c, flete=200.0, operacion_id=oid)
    assert r.status_code == 500, r.text
    assert open(ruta, "rb").read() == entregado, "el archivo ya entregado cambió con una regeneración que falló"
    assert _archivos(u) == [archivo] and _operaciones(u) == antes and _leer(u)["ops"] == 1
