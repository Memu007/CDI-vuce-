"""COBRO-CORTE-1: cuándo se cuenta una operación y dónde se corta el servicio.

- Una cuenta impaga, vencida o cancelada no genera ni gasta Gemini: 402 en las
  rutas que gastan Gemini o generan valor, con la razón real en el aviso.
- El tope del plan se mira sólo donde se cuenta una operación: la primera vez
  que se genera el MARIA de un `operation_id`. Con el tope lleno se puede
  validar, volver a generar y bajar lo ya contado, y guardarlo en el cliente.
- Regenerar el mismo id no cuenta; un id no pasa de 10 contenidos distintos.
- Guardar después de generar usa la misma operación y no cuenta otra vez.

Cada caso usa su propia cuenta (registro y login, sin override) y datos
inventados. Las carreras van contra un Postgres local en
`scripts/testing/cobro_corte1_postgres.py`.
"""
import asyncio
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
ARCHIVO_A = f"MARIA_{ID_A}.TXT"


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
            return [{"id": o.id, "op_code": o.op_code, "archivo": o.generated_file,
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


def _generar(c, operation_id=ID_A, flete=7925.0):
    pedido = _pedido()
    pedido["operation_id"] = operation_id
    pedido["flete"] = flete
    return c.post("/generate_maria", json=pedido)


def _cliente(c):
    r = c.post("/api/clientes", json={"nombre": "Importadora Inventada", "cuit": "30999999995"})
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _guardar(c, client_id, operation_id):
    return c.post(f"/api/clientes/{client_id}/operaciones", json={
        "operation_id": operation_id, "source": "maria",
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
    "suscripcion_vencida": ({"billing_status": "active", "trial_ends_at": AHORA - timedelta(days=10)},
                            "TRIAL_EXPIRED", "Venció tu suscripción", "past_due"),
    # COBRO-MP-2: la cancelada sigue hasta el fin del período; después, se corta.
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
    assert c.get(f"/download/{ARCHIVO_A}").status_code == 404


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
    """COBRO-MP-2 (C2): cancelar no corta lo que ya se pagó."""
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


@pytest.mark.parametrize("estado", list(ESTADOS))
def test_regenerar_lo_ya_contado_con_la_cuenta_que_no_esta_al_dia_da_402(cuenta, estado):
    # Lo ya contado no pasa por el tope, pero sí por el estado.
    c, u = cuenta()
    assert _generar(c).status_code == 200
    campos, code, _, _ = ESTADOS[estado]
    _fijar(u, **campos)
    r = _generar(c, flete=8000.0)
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == code
    assert len(_operaciones(u)[0]["extra"]["maria_hashes"]) == 1


@pytest.mark.parametrize("estado", list(ESTADOS))
def test_guardar_lo_ya_generado_con_la_cuenta_que_no_esta_al_dia_da_402(cuenta, estado):
    c, u = cuenta()
    assert _generar(c).status_code == 200
    cid = _cliente(c)
    campos, code, _, _ = ESTADOS[estado]
    _fijar(u, **campos)
    r = _guardar(c, cid, ARCHIVO_A)
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == code
    assert _operaciones(u)[0]["cliente"] is None


# ------------------------------------------------------------ cuándo se cuenta


def test_generar_cuenta_una_vez_por_id_y_crea_la_operacion(cuenta):
    c, u = cuenta()
    r = _generar(c)
    assert r.status_code == 200, r.text
    assert r.json()["filename"] == ARCHIVO_A
    assert _leer(u)["ops"] == 1
    ops = _operaciones(u)
    assert len(ops) == 1, ops
    assert ops[0]["archivo"] == ARCHIVO_A and ops[0]["op_code"] == "OP-000001", ops
    assert ops[0]["source"] == "maria" and ops[0]["cliente"] is None, ops

    # La misma descarga otra vez no cuenta ni crea otra.
    assert _generar(c).status_code == 200
    assert _leer(u)["ops"] == 1
    assert len(_operaciones(u)) == 1

    # Otro id es otra operación, con el código siguiente.
    assert _generar(c, operation_id="FAC_CORTE1B").status_code == 200
    assert _leer(u)["ops"] == 2
    assert [o["op_code"] for o in _operaciones(u)] == ["OP-000001", "OP-000002"]


def test_el_mismo_id_no_pasa_de_10_contenidos_distintos(cuenta):
    c, u = cuenta()
    for i in range(10):
        r = _generar(c, flete=7925.0 + i)
        assert r.status_code == 200, (i, r.text)
    decimo = c.get(f"/download/{ARCHIVO_A}")
    assert decimo.status_code == 200
    assert _leer(u)["ops"] == 1

    r = _generar(c, flete=9999.0)
    assert r.status_code == 409, r.text
    detalle = r.json()["detail"]
    assert detalle["code"] == "MARIA_REGENERACIONES_AGOTADAS", detalle
    assert "10" in detalle["message"], detalle
    # No pisó el archivo ni contó.
    assert c.get(f"/download/{ARCHIVO_A}").content == decimo.content
    assert _leer(u)["ops"] == 1
    assert len(_operaciones(u)[0]["extra"]["maria_hashes"]) == 10

    # Un contenido que ya se generó sigue saliendo.
    assert _generar(c, flete=7925.0 + 3).status_code == 200
    assert _leer(u)["ops"] == 1


def test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado(cuenta):
    c, u = cuenta()
    assert _generar(c).status_code == 200
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20),
           ops_used_this_period=15, extra_ops_remaining=0)

    assert c.post("/generate_maria/avisos", json=_pedido()).status_code == 200
    assert c.post("/api/validate/smart", json={"items": [
        {"descripcion": "Lona de PVC", "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}]}
    ).status_code == 200
    assert c.get(f"/download/{ARCHIVO_A}").status_code == 200
    # Volver a generar la operación ya contada, igual o corregida, sale.
    assert _generar(c).status_code == 200
    assert _generar(c, flete=8000.0).status_code == 200
    # Guardarla en el cliente también.
    cid = _cliente(c)
    r = _guardar(c, cid, ARCHIVO_A)
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 15

    # Una operación nueva, no.
    r = _generar(c, operation_id="FAC_CORTE1NUEVA")
    assert r.status_code == 402, r.text
    detalle = r.json()["detail"]
    assert detalle["code"] == "PLAN_LIMIT_EXCEEDED", detalle
    assert "límite de 15" in detalle["message"], detalle
    assert c.get("/download/MARIA_FAC_CORTE1NUEVA.TXT").status_code == 404
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


# ------------------------------------------------------------ guardar después


def test_guardar_despues_de_generar_no_cuenta_dos_veces(cuenta):
    c, u = cuenta()
    assert _generar(c).status_code == 200
    assert _leer(u)["ops"] == 1
    cid = _cliente(c)
    r = _guardar(c, cid, ARCHIVO_A)
    assert r.status_code == 200, r.text
    ops = _operaciones(u)
    assert len(ops) == 1, ops
    assert r.json()["operation_id"] == ops[0]["id"]
    assert r.json()["op_code"] == ops[0]["op_code"] == "OP-000001"
    assert ops[0]["cliente"] == cid and ops[0]["archivo"] == ARCHIVO_A
    assert ops[0]["extra"]["resumen"]["valor_total"] == 1387.5
    assert len(ops[0]["extra"]["maria_hashes"]) == 1
    assert _leer(u)["ops"] == 1

    # Volver a generar después de guardar tampoco cuenta.
    assert _generar(c).status_code == 200
    assert _leer(u)["ops"] == 1


def test_guardar_sin_haber_generado_cuenta_una(cuenta):
    c, u = cuenta()
    cid = _cliente(c)
    r = _guardar(c, cid, "MARIA_FAC_NUNCA.TXT")
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 1
    assert len(_operaciones(u)) == 1


def test_guardar_con_el_archivo_de_otra_cuenta_no_toca_su_operacion(cuenta):
    a, ua = cuenta()
    b, ub = cuenta()
    assert _generar(a).status_code == 200
    cid = _cliente(b)
    r = _guardar(b, cid, ARCHIVO_A)
    assert r.status_code == 200, r.text
    assert _leer(ub)["ops"] == 1
    ops_a = _operaciones(ua)
    assert len(ops_a) == 1 and ops_a[0]["cliente"] is None, ops_a
    assert _operaciones(ub)[0]["id"] != ops_a[0]["id"]


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
    assert _generar(c).status_code == 200
    cid = _cliente(c)
    assert _guardar(c, cid, ARCHIVO_A).status_code == 200
    assert _guardar(c, cid, ARCHIVO_A).status_code == 200
    ops = _operaciones(u)
    assert len(ops) == 1 and _items(ops[0]["id"]) == 1
    assert _leer(u)["ops"] == 1


def test_guardar_con_un_id_que_no_es_un_maria_no_lo_toma_como_archivo(cuenta):
    # Sólo MARIA_<id>.TXT busca la operación generada: otro id cuenta una
    # operación nueva cada vez, como antes de COBRO-CORTE-1.
    c, u = cuenta()
    cid = _cliente(c)
    assert _guardar(c, cid, "OP_SIN_ARCHIVO").status_code == 200
    assert _guardar(c, cid, "OP_SIN_ARCHIVO").status_code == 200
    ops = _operaciones(u)
    assert [o["archivo"] for o in ops] == [None, None], ops
    assert _leer(u)["ops"] == 2


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


# ------------------------------------------------------------ exportación (B)


def _exportar(c, operation_id="FAC_CORTE1EXP", flete=100.0):
    from tests.test_maria1b_devolucion import EXPORT
    return c.post("/generate_maria_export", json={**EXPORT, "operation_id": operation_id, "flete": flete})


def test_la_exportacion_cuenta_una_vez_por_operacion(cuenta):
    # COBRO-MP-1, B: la D4 b es «el MARIA de un operation_id»; la
    # exportación también cuenta, con la misma regla que la importación.
    c, u = cuenta()
    r = _exportar(c)
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 1, "la exportación no cuenta la operación"
    assert _exportar(c).status_code == 200
    assert _exportar(c, flete=200.0).status_code == 200
    assert _leer(u)["ops"] == 1, "volver a exportar la misma operación cuenta otra vez"
    ops = _operaciones(u)
    assert [o["archivo"] for o in ops] == [r.json()["filename"]], ops
    assert len(ops[0]["extra"]["maria_hashes"]) == 2, ops


def test_con_el_tope_lleno_la_exportacion_nueva_da_402_y_la_ya_contada_sale(cuenta):
    c, u = cuenta()
    archivo = _exportar(c).json()["filename"]
    _fijar(u, billing_status="active", trial_ends_at=AHORA + timedelta(days=20),
           ops_used_this_period=15, extra_ops_remaining=0)
    assert _exportar(c, flete=300.0).status_code == 200
    r = _exportar(c, operation_id="FAC_CORTE1EXPNUEVA")
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "PLAN_LIMIT_EXCEEDED", r.json()
    assert c.get("/download/" + archivo.replace("FAC_CORTE1EXP", "FAC_CORTE1EXPNUEVA")).status_code == 404
    assert _leer(u)["ops"] == 15
    assert len(_operaciones(u)) == 1


@pytest.mark.parametrize("largo", [43, 44, 50, 60])
def test_la_exportacion_con_un_id_largo_cuenta_una_vez(cuenta, largo):
    # COBRO-MP-1 vuelta 2, g: con 44 a 50 caracteres el archivo no se
    # reconocía como un MARIA y cada exportación contaba otra operación.
    c, u = cuenta()
    operation_id = ("FAC" + "9" * largo)[:largo]
    r = _exportar(c, operation_id=operation_id)
    assert r.status_code == 200, r.text
    assert _exportar(c, operation_id=operation_id, flete=200.0).status_code == 200
    assert _leer(u)["ops"] == 1, "volver a exportar el mismo id largo cuenta otra vez"
    cid = _cliente(c)
    assert _guardar(c, cid, r.json()["filename"]).status_code == 200
    assert _leer(u)["ops"] == 1, "guardar la exportación de id largo cuenta otra vez"
    assert len(_operaciones(u)) == 1


def test_una_importacion_con_id_export_no_reusa_la_exportacion(cuenta):
    # g: la importación «EXPORT_<x>» y la exportación «<x>» daban el mismo
    # archivo: la segunda completaba la operación de la primera sin contar.
    c, u = cuenta()
    assert _exportar(c, operation_id="FAC_CORTE1X").status_code == 200
    r = _generar(c, operation_id="EXPORT_FAC_CORTE1X")
    assert r.status_code == 200, r.text
    assert _leer(u)["ops"] == 2, "la importación reusó la operación de la exportación"
    assert len({o["archivo"] for o in _operaciones(u)}) == 2, _operaciones(u)
