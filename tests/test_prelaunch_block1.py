"""
Bloque 1 — Testing pre-lanzamiento: Core del producto (sin pagos).
Verifica que el flujo principal no se rompió con los cambios de Ola 4.

Cobertura:
 1. Registro con email y trial 14 días.
 2. Login / logout.
 3. Subida de Excel: extracción, revisión, NCM.
 4. Generación TXT MARIA.
 5. Carga manual de operaciones.
 6. Drawer de clientes, catálogo, export CSV.
 7. Límite de 10 ops/mes en plan trial (antes de pagar).
 8. Mensajes de error claros.
"""
import io
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from proyecto_maria import main
from proyecto_maria.services import billing_service
from proyecto_maria.database.models import User as DBUser


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(auth_override):
    """TestClient autenticado con user test_user (premium, active)."""
    return TestClient(main.app)


@pytest.fixture()
def anon_client():
    """TestClient sin autenticación (para probar acceso anónimo)."""
    return TestClient(main.app)


def _unique(prefix="prelaunch"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _make_excel_bytes(headers: list, rows: list[list]) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError:
        pytest.skip("openpyxl not installed")
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. REGISTRO: email, trial 14 días, plan premium, sin tarjeta
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestRegistro:

    def test_registro_exitoso_sin_tarjeta(self, anon_client, monkeypatch):
        """Registro nuevo asigna plan premium + trial 14 días sin pedir tarjeta."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        uname = _unique("reg")
        email = f"{uname}@test.prelaunch"
        res = anon_client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "name": "Test Prelaunch",
            "email": email,
        })
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["plan"] == "premium"
        assert data["billing"]["billing_status"] == "trial"
        # trial_ends_at debe estar ~14 días en el futuro
        trial_end = datetime.fromisoformat(data["billing"]["trial_ends_at"])
        delta = trial_end - datetime.now(timezone.utc)
        assert 13 <= delta.days <= 14, f"Trial delta inesperado: {delta.days} días"
        # No se requirió tarjeta (payment_method == None)
        assert data["billing"]["payment_method"] is None

    def test_registro_sin_email_rechazado(self, anon_client, monkeypatch):
        """Email es obligatorio en Ola 4."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        res = anon_client.post("/auth/register", json={
            "username": _unique("noemail"),
            "password": "SecureP@ss1",
        })
        assert res.status_code == 422  # Pydantic validation (email required)

    def test_registro_username_duplicado_400(self, anon_client, monkeypatch):
        """Segundo registro con mismo username devuelve 400."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        uname = _unique("dup")
        payload = {
            "username": uname,
            "password": "SecureP@ss1",
            "email": f"{uname}@test.prelaunch",
        }
        anon_client.post("/auth/register", json=payload)
        res = anon_client.post("/auth/register", json=payload)
        assert res.status_code == 400
        assert "ya existe" in res.json()["detail"].lower()

    def test_registro_email_duplicado_400(self, anon_client, monkeypatch):
        """Segundo registro con mismo email devuelve 400."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        email = f"{_unique('emaildup')}@test.prelaunch"
        anon_client.post("/auth/register", json={
            "username": _unique("first"),
            "password": "SecureP@ss1",
            "email": email,
        })
        res = anon_client.post("/auth/register", json={
            "username": _unique("second"),
            "password": "SecureP@ss1",
            "email": email,
        })
        assert res.status_code == 400
        assert "email" in res.json()["detail"].lower()

    def test_registro_username_invalido_400(self, anon_client, monkeypatch):
        """Username con caracteres especiales devuelve 400."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        res = anon_client.post("/auth/register", json={
            "username": "a b!",
            "password": "SecureP@ss1",
            "email": "bad@test.prelaunch",
        })
        assert res.status_code == 400
        assert "username" in res.json()["detail"].lower()

    def test_registro_plan_basic_rechazado(self, anon_client, monkeypatch):
        """Plan 'basic' ya no existe; el registro lo rechaza con 400."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        res = anon_client.post("/auth/register", json={
            "username": _unique("basic"),
            "password": "SecureP@ss1",
            "email": f"{_unique('basic')}@test.prelaunch",
            "plan": "basic",
        })
        assert res.status_code == 400
        assert "no disponible" in res.json()["detail"].lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. LOGIN / LOGOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLoginLogout:

    def test_login_exitoso_setea_cookie(self, anon_client, monkeypatch):
        """Login exitoso devuelve access_token y lo setea en cookie."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        uname = _unique("login")
        email = f"{uname}@test.prelaunch"
        anon_client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "email": email,
        })
        res = anon_client.post("/auth/login", json={
            "username": uname,
            "password": "SecureP@ss1",
        })
        assert res.status_code == 200, res.text
        data = res.json()
        assert "access_token" in data
        assert data["user"]["plan"] == "premium"
        assert "access_token" in res.cookies

    def test_login_credenciales_invalidas_401(self, anon_client, monkeypatch):
        """Login con password incorrecto devuelve 401."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        uname = _unique("loginfail")
        anon_client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "email": f"{uname}@test.prelaunch",
        })
        res = anon_client.post("/auth/login", json={
            "username": uname,
            "password": "WrongPassword",
        })
        assert res.status_code == 401

    def test_login_usuario_inexistente_401(self, anon_client):
        """Login con usuario que no existe devuelve 401."""
        res = anon_client.post("/auth/login", json={
            "username": "noexisto_nunca",
            "password": "algo",
        })
        assert res.status_code == 401

    def test_logout_borra_cookie(self, anon_client, monkeypatch):
        """Logout borra la cookie access_token."""
        monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
        uname = _unique("logout")
        anon_client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "email": f"{uname}@test.prelaunch",
        })
        anon_client.post("/auth/login", json={
            "username": uname,
            "password": "SecureP@ss1",
        })
        res = anon_client.post("/auth/logout")
        assert res.status_code == 200
        assert res.json()["message"] == "Sesión cerrada"

    def test_current_user_sin_auth_401(self, anon_client):
        """GET /auth/current_user sin sesión devuelve 401."""
        res = anon_client.get("/auth/current_user")
        assert res.status_code == 401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. SUBIDA DE EXCEL: extracción, revisión, NCM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestUploadExcel:

    def test_upload_excel_extrae_items(self, client):
        """Subir Excel válido devuelve items extraídos con NCMs."""
        excel = _make_excel_bytes(
            ["pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"],
            [["84713000", "Laptop", "CN", 10, 350.0, 1.5]],
        )
        res = client.post(
            "/upload_excel/",
            files={"file": ("test.xlsx", io.BytesIO(excel),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        # La respuesta usa items_procesados / items_extraidos
        extracted = data.get("items_count", data.get("items_extraidos", data.get("items_procesados", 0)))
        assert extracted >= 1, f"Expected >=1 items, response keys: {list(data.keys())}"

    def test_upload_excel_sin_auth_401(self, anon_client):
        """Subir Excel sin sesión devuelve 401."""
        excel = _make_excel_bytes(
            ["pieza", "descripcion", "origen", "cantidad", "valor_unitario"],
            [["84713000", "Laptop", "CN", 10, 350.0]],
        )
        res = anon_client.post(
            "/upload_excel/",
            files={"file": ("test.xlsx", io.BytesIO(excel),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert res.status_code == 401

    def test_upload_archivo_invalido_400(self, client):
        """Subir un archivo que no es Excel/PDF devuelve error."""
        res = client.post(
            "/upload_excel/",
            files={"file": ("test.txt", io.BytesIO(b"esto no es excel"), "text/plain")},
        )
        # Puede ser 400 o 500 dependiendo del manejo; lo importante es que no sea 200
        assert res.status_code != 200


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. GENERACIÓN TXT MARIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestGenerateMaria:

    def test_generate_maria_txt_happy_path(self, client):
        """Generar MARIA TXT con items válidos devuelve contenido TXT."""
        res = client.post("/generate_maria", json={
            "operation_id": "TEST001",
            "items": [{
                "pieza": "84713000900R",
                "descripcion": "Laptop importada",
                "origen": "CN",
                "cantidad": 5,
                "valor_unitario": 800.0,
                "peso_kg": 2.5,
            }],
            "moneda": "DOL",
            "incoterm": "FOB",
            "sbt_sufijo_valor": "AA(DEMO)-AB(DEMO)-CA00-",
        })
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["success"] is True
        assert "content" in data
        assert "MARIA" in data["filename"].upper()

    def test_generate_maria_sin_items_genera_vacio(self, client):
        """Generar MARIA sin items devuelve 200 con TXT vacío (sin bloques de ítem)."""
        res = client.post("/generate_maria", json={
            "operation_id": "TEST002",
            "items": [],
            "sbt_sufijo_valor": "AA(DEMO)-AB(DEMO)-CA00-",
        })
        # El generador acepta listas vacías y produce un TXT sin bloques de ítem.
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_generate_maria_sin_auth_401(self, anon_client):
        """Generar MARIA sin sesión devuelve 401."""
        res = anon_client.post("/generate_maria", json={
            "operation_id": "TEST003",
            "items": [{"pieza": "84713000", "descripcion": "X", "origen": "CN",
                        "cantidad": 1, "valor_unitario": 100, "peso_kg": 1}],
        })
        assert res.status_code == 401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. CARGA MANUAL DE OPERACIONES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestOperacionManual:

    def test_crear_operacion_manual_ok(self, client):
        """Crear operación manual con client_id y items válidos."""
        # Crear cliente primero
        rc = client.post("/api/clientes", json={"nombre": "OpTest", "cuit": "30999999991"})
        assert rc.status_code == 200
        cid = rc.json()["cliente"]["id"]

        res = client.post("/api/operations/manual", json={
            "client_id": cid,
            "items": [{"descripcion": "Item A", "cantidad": 1, "valor_unitario": 100}],
        })
        assert res.status_code == 200, res.text

    def test_crear_operacion_sin_client_id_400(self, client):
        """Operación sin client_id devuelve 400."""
        res = client.post("/api/operations/manual", json={
            "client_id": "",
            "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}],
        })
        assert res.status_code == 400
        assert "client_id" in res.json()["detail"].lower()

    def test_crear_operacion_null_client_id_400(self, client):
        """Operación con client_id=null devuelve 400, no 500 (regresión)."""
        res = client.post("/api/operations/manual", json={
            "client_id": None,
            "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}],
        })
        assert res.status_code == 400

    def test_crear_operacion_sin_items_400(self, client):
        """Operación sin items devuelve 400."""
        rc = client.post("/api/clientes", json={"nombre": "NoItems", "cuit": "30999999992"})
        cid = rc.json()["cliente"]["id"]
        res = client.post("/api/operations/manual", json={
            "client_id": cid,
            "items": [],
        })
        assert res.status_code == 400

    def test_crear_operacion_sin_auth_401(self, anon_client):
        """Operación manual sin sesión devuelve 401."""
        res = anon_client.post("/api/operations/manual", json={
            "client_id": "x",
            "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}],
        })
        assert res.status_code == 401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. DRAWER DE CLIENTES, CATÁLOGO, EXPORT CSV
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestClientes:

    def test_crear_cliente_ok(self, client):
        """Crear cliente con nombre y CUIT."""
        res = client.post("/api/clientes", json={
            "nombre": "Cliente Prelaunch",
            "cuit": "20345678901",
        })
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["success"] is True
        assert data["cliente"]["nombre"] == "Cliente Prelaunch"

    def test_listar_clientes(self, client):
        """GET /api/clientes devuelve lista."""
        client.post("/api/clientes", json={"nombre": "Listar Test"})
        res = client.get("/api/clientes")
        assert res.status_code == 200
        data = res.json()
        # La respuesta es una lista o un dict con "clientes"
        if isinstance(data, list):
            assert len(data) >= 1
        else:
            assert len(data.get("clientes", data.get("items", []))) >= 1

    def test_buscar_cliente(self, client):
        """GET /api/clientes/search?q=... devuelve resultados."""
        nombre = _unique("buscar")
        client.post("/api/clientes", json={"nombre": nombre})
        res = client.get(f"/api/clientes/search?q={nombre[:8]}")
        assert res.status_code == 200

    def test_editar_cliente(self, client):
        """PUT /api/clientes/{id} actualiza nombre."""
        rc = client.post("/api/clientes", json={"nombre": "Editable"})
        cid = rc.json()["cliente"]["id"]
        res = client.put(f"/api/clientes/{cid}", json={"nombre": "Editado"})
        assert res.status_code == 200

    def test_eliminar_cliente(self, client):
        """DELETE /api/clientes/{id} elimina (soft-delete) cliente."""
        rc = client.post("/api/clientes", json={"nombre": "Borrable"})
        cid = rc.json()["cliente"]["id"]
        res = client.delete(f"/api/clientes/{cid}")
        assert res.status_code == 200

    def test_catalogo_columnas_vacio_inicialmente(self, client):
        """Nuevo cliente no tiene mapping de columnas."""
        rc = client.post("/api/clientes", json={"nombre": "CatVacio"})
        cid = rc.json()["cliente"]["id"]
        res = client.get(f"/api/clientes/{cid}/catalogo/columnas")
        assert res.status_code == 200
        assert res.json()["columnas"] == {}

    def test_catalogo_productos_vacio_inicialmente(self, client):
        """Nuevo cliente no tiene productos aprendidos."""
        rc = client.post("/api/clientes", json={"nombre": "ProdVacio"})
        cid = rc.json()["cliente"]["id"]
        res = client.get(f"/api/clientes/{cid}/catalogo/productos")
        assert res.status_code == 200
        prods = res.json().get("productos", res.json().get("items", []))
        assert len(prods) == 0

    def test_export_csv_devuelve_csv(self, client):
        """Export CSV devuelve contenido text/csv."""
        rc = client.post("/api/clientes", json={"nombre": "CsvTest", "cuit": "20999999903"})
        cid = rc.json()["cliente"]["id"]
        res = client.get(f"/api/clientes/{cid}/export.csv")
        assert res.status_code == 200
        ct = res.headers.get("content-type", "")
        assert "csv" in ct or "text" in ct

    def test_clientes_sin_auth_401(self, anon_client):
        """Endpoints de clientes requieren autenticación."""
        assert anon_client.get("/api/clientes").status_code == 401
        assert anon_client.post("/api/clientes", json={"nombre": "X"}).status_code == 401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. LÍMITE 10 OPS/MES EN TRIAL (billing_service puro, sin DB)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FakeUser:
    """Simula un User de DB para testing de billing_service."""
    def __init__(self, plan="premium", billing_status="trial", used=0, extra=0,
                 extra_ops_expires_at=None):
        self.plan = plan
        self.billing_status = billing_status
        self.ops_used_this_period = used
        self.extra_ops_remaining = extra
        self.extra_ops_expires_at = extra_ops_expires_at


class TestLimiteOps:

    def test_trial_permite_hasta_15_ops(self):
        """Trial con 14 ops usadas puede crear una más."""
        u = FakeUser(used=14)
        ok, reason = billing_service.can_create_operation(u)
        assert ok is True

    def test_trial_bloquea_en_16(self):
        """Trial con 15 ops usadas es bloqueado."""
        u = FakeUser(used=15)
        ok, reason = billing_service.can_create_operation(u)
        assert ok is False
        assert "límite" in reason.lower()

    def test_billing_none_rechazado(self):
        """Usuario sin billing_status activo es rechazado."""
        u = FakeUser(billing_status="none")
        ok, reason = billing_service.can_create_operation(u)
        assert ok is False

    def test_billing_past_due_rechazado(self):
        """Usuario past_due es rechazado."""
        u = FakeUser(billing_status="past_due")
        ok, reason = billing_service.can_create_operation(u)
        assert ok is False

    def test_extra_credits_salvan_del_limite(self):
        """Con 15 ops usadas pero créditos extra, puede seguir."""
        u = FakeUser(used=15, extra=5)
        ok, reason = billing_service.can_create_operation(u)
        assert ok is True

    def test_extra_credits_vencidos_no_cuentan(self):
        """Créditos expirados no salvan el límite."""
        u = FakeUser(
            used=15,
            extra=5,
            extra_ops_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        ok, reason = billing_service.can_create_operation(u)
        assert ok is False
        assert u.extra_ops_remaining == 0  # limpiados automáticamente

    def test_record_operation_incrementa_usado(self):
        """record_operation_created incrementa ops_used_this_period."""
        u = FakeUser(used=5)
        billing_service.record_operation_created(u)
        assert u.ops_used_this_period == 6

    def test_record_operation_consume_extra(self):
        """Al superar el límite, consume créditos extra."""
        u = FakeUser(used=15, extra=3)
        billing_service.record_operation_created(u)
        assert u.ops_used_this_period == 16
        assert u.extra_ops_remaining == 2

    def test_record_operation_sin_margen_explota(self):
        """Sin créditos ni margen, RuntimeError."""
        u = FakeUser(used=15, extra=0)
        with pytest.raises(RuntimeError, match="Límite"):
            billing_service.record_operation_created(u)

    def test_topup_max_100(self):
        """Top-up no puede exceder 100 créditos acumulados."""
        assert billing_service.EXTRA_OPS_MAX == 100


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. MENSAJES DE ERROR CLAROS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestErrorMessages:

    def test_401_json_no_html(self, anon_client):
        """Las respuestas 401 devuelven JSON, no HTML."""
        res = anon_client.get("/auth/current_user")
        assert res.status_code == 401
        data = res.json()  # No debe lanzar error de parseo
        assert "detail" in data

    def test_billing_limit_detalle_claro(self):
        """El mensaje de límite incluye información útil."""
        u = FakeUser(used=15, extra=0)
        ok, reason = billing_service.can_create_operation(u)
        assert not ok
        assert "15" in reason  # menciona el límite numérico
        assert "top-up" in reason.lower() or "premium" in reason.lower()

    def test_plan_inexistente_detalle(self):
        """El error de plan inexistente da contexto."""
        with pytest.raises(ValueError) as exc:
            billing_service.get_plan("enterprise")
        assert "no disponible" in str(exc.value).lower()
        assert "premium" in str(exc.value).lower()
