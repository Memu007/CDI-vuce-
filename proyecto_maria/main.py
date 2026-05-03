# admin_router imported at line 58
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header, Request, Response, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx # Para consultas externas async
from dotenv import load_dotenv

# Cargar variables de entorno desde el directorio padre (CDI/.env)
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

# Archivos de datos
DATA_DIR = os.path.join(basedir, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
BACKUP_FILE = os.path.join(DATA_DIR, 'localStorage_backup.json')

# Configuración de Templates
templates = Jinja2Templates(directory=os.path.join(basedir, "proyecto_maria", "templates"))

# Versión del proyecto (se actualiza al reiniciar el servidor para cache busting)
PROJECT_VERSION = datetime.now().strftime("%Y%m%d%H%M%S")

# NOTA: `clientes.json` y `ncm_notas.json` ya no se usan. Los clientes
# y notas viven en la DB (tabla `clients` y `ncm_notes`) con
# `owner_username` para aislamiento multi-tenant. Ver
# `docs/AUDIT_MULTITENANT.md`.

from proyecto_maria.models.operations import OperationPayload, Item
from proyecto_maria.core.validations import run_pre_maria_validations, run_smart_validations
from proyecto_maria.core.excel_generator import create_maria_excel
from proyecto_maria.core.maria_generator import generate_maria_txt, validate_items_for_maria
from proyecto_maria.pdf_extractor import process_pdf  # Importar el extractor
import pandas as pd
from proyecto_maria.core.vuce_connector import get_ncm_data  # VUCE activo en modo mock
from proyecto_maria.routers import admin_router

# ============== Configuración de Autenticación ==============
_DEFAULT_DEV_SECRET = "tu-clave-secreta-super-segura-cambiar-en-produccion"
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", _DEFAULT_DEV_SECRET)
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# --- SECURITY CHECK reforzado ---
# 1) Default dev key nunca puede usarse en prod.
# 2) Key demasiado corta (<32) es insegura para HS256, fail en prod, warn en dev.
# 3) En dev, log visible si estamos usando la default para no olvidarse al
#    pasar a prod.
_known_weak_substrings = ("cambiar-en-produccion", "changeme", "secret", "default", "12345")
_is_default_key = SECRET_KEY == _DEFAULT_DEV_SECRET
_is_obviously_weak = any(w in SECRET_KEY.lower() for w in _known_weak_substrings)
_is_too_short = len(SECRET_KEY) < 32

if IS_PRODUCTION and (_is_default_key or _is_obviously_weak or _is_too_short):
    raise ValueError(
        "CRITICAL SECURITY ERROR: running in PRODUCTION with an insecure "
        "JWT_SECRET_KEY. Requirements: >=32 chars, no obvious words "
        "('secret', 'changeme', 'default', etc). Set JWT_SECRET_KEY in .env."
    )
elif _is_default_key or _is_obviously_weak or _is_too_short:
    import warnings
    warnings.warn(
        "Usando SECRET_KEY debil en dev. Antes de ir a produccion "
        "generar una clave fuerte con: python -c 'import secrets; "
        "print(secrets.token_urlsafe(48))'",
        RuntimeWarning, stacklevel=2,
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Importar middleware de seguridad
try:
    from proyecto_maria.security.security_middleware import EnhancedSecurityHeadersMiddleware
except ImportError:
    from security.security_middleware import EnhancedSecurityHeadersMiddleware

security = HTTPBearer()

# ============== Configuración de Base de Datos ==============
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from proyecto_maria.database.connection import get_async_session, init_db
from proyecto_maria.database.models import User, Client, PasswordResetToken
import uuid
import logging
from passlib.context import CryptContext

from proyecto_maria.core.rate_limit import limiter, get_dynamic_rate_limit
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Dependency to get DB session
async def get_db():
    async for session in get_async_session():
        yield session

def send_email(to_email: str, subject: str, body: str):
    """Envía un email usando SMTP"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM_EMAIL")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password, smtp_from]):
        print("=" * 60, flush=True)
        print("MOCK EMAIL - SMTP no configurado", flush=True)
        print("=" * 60, flush=True)
        print(f"To: {to_email}", flush=True)
        print(f"Subject: {subject}", flush=True)
        print("-" * 60, flush=True)
        print("Body (HTML):", flush=True)
        print(body, flush=True)
        print("=" * 60, flush=True)
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email enviado correctamente a {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False


# ============== FRONTEND URL HELPER ==============
# FRONTEND_URL es la base publica desde la que se sirve la UI. Usada para
# armar links en emails (reset password, verificacion). En prod ES OBLIGATORIO
# que venga del .env apuntando al dominio real. En dev default a localhost.
def get_frontend_url() -> str:
    url = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    if url:
        return url
    if IS_PRODUCTION:
        # Fail fast: mandar un email con link a localhost es un bug silencioso
        # que vuelve el reset de password inutil.
        raise RuntimeError(
            "FRONTEND_URL no esta seteada en .env y estamos en produccion. "
            "Definir p.ej. FRONTEND_URL=https://cdi.tu-dominio.com"
        )
    return "http://127.0.0.1:8010"


def _email_verification_enabled() -> bool:
    """Toggle para exigir verificacion de email en el registro.

    Default en dev: OFF (para no bloquear testers).
    En prod se recomienda prender con EMAIL_VERIFICATION_REQUIRED=true.
    """
    return os.getenv("EMAIL_VERIFICATION_REQUIRED", "false").lower() == "true"


def build_email_verification_token(username: str) -> str:
    """Firma un JWT dedicado para verificacion de email (24h).

    type=email_verification para no confundirlo con el access token.
    """
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode(
        {"sub": username, "type": "email_verification", "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def send_verification_email(username: str, email: str, display_name: str | None = None) -> bool:
    """Envia email con link para verificar la direccion del user.

    Recibe strings (no el objeto ORM) porque esta funcion se ejecuta como
    BackgroundTask y la sesion SQLAlchemy ya puede estar cerrada/expirada
    cuando corre.

    Devuelve True si SMTP confirmo envio, False si quedo en modo mock o
    si hubo error.
    """
    if not email:
        return False
    try:
        token = build_email_verification_token(username)
        link = f"{get_frontend_url()}/auth/verify-email?token={token}"
        body = f"""
        <h1>Verificá tu email</h1>
        <p>Hola {display_name or username},</p>
        <p>Para activar tu cuenta en CDI hacé clic en el siguiente enlace:</p>
        <p><a href="{link}">Verificar email</a></p>
        <p>El link expira en 24 horas.</p>
        <br>
        <p>Si no fuiste vos, ignorá este mensaje.</p>
        """
        return send_email(email, "Verificá tu cuenta - CDI", body)
    except Exception as e:
        # No romper la task de background si algo sale mal (ej. user sin
        # email, FRONTEND_URL invalido, etc).
        logging.exception(f"send_verification_email failed for {username}: {e}")
        return False


class LoginRequest(BaseModel):
    username: str
    password: str

class CardInput(BaseModel):
    cardholder: str
    number: str
    exp: str           # "MM/YY" o "MM/YYYY"
    cvc: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str = None  # Optional, defaults to username
    email: str  # REQUIRED - needed for password recovery
    plan: str = "trial"
    # Opcional: si viene, se valida y se arranca trial 14d con PM simulado.
    # Si no viene, user queda con billing_status='none' y sin trial activo.
    payment_method: CardInput | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

def create_access_token(data: dict):
    """Crea un token JWT con expiración"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

app = FastAPI(
    title="Optimizador de Carga para Sistema MARIA",
    description="Un proyecto para validar, enriquecer y generar archivos de carga para despachantes de aduana.",
    version="0.2.0 (Con Interfaz Web)",
)

# Configurar CORS (OWASP A5 - Broken Access Control)
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# CORS + cookies: la especificacion prohibe combinar allow_origins=["*"]
# con allow_credentials=True (los browsers rechazan la cookie). Como la
# app usa JWT en cookie HttpOnly, necesitamos allow_credentials=True, por
# lo tanto allow_origins NUNCA puede ser "*".
# Default de dev: permitir localhost + 127.0.0.1 en puertos comunes.
# Prod: ALLOWED_ORIGINS debe venir del .env con la URL real del frontend.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
if _raw_origins and _raw_origins != "*":
    allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
elif IS_PRODUCTION:
    # En prod sin ALLOWED_ORIGINS explicito, fallamos fuerte: es una mala
    # config que dejaria el sistema inaccesible o inseguro.
    raise ValueError(
        "CORS config error: ALLOWED_ORIGINS no puede ser vacio ni '*' en "
        "produccion porque la app usa cookies. Definir p.ej.: "
        "ALLOWED_ORIGINS=https://cdi.tu-dominio.com"
    )
else:
    # Defaults de desarrollo local. Cubrimos los puertos tipicos en los que
    # corre el server (8000/8010/8011) y herramientas como Live Server.
    allowed_origins = [
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:8010", "http://127.0.0.1:8010",
        "http://localhost:8011", "http://127.0.0.1:8011",
        "http://localhost:5555", "http://127.0.0.1:5555",
        "http://localhost:5500", "http://127.0.0.1:5500",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Configurar Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ----- Handlers globales: dejar mensaje amigable al user en 5xx,
# registrar el detalle tecnico en logs para Railway. Errores 4xx
# (validaciones, auth, conflictos) se devuelven tal cual.
from fastapi.responses import JSONResponse

_FRIENDLY_5XX = (
    "No pudimos procesar tu solicitud. "
    "Probá de nuevo en unos segundos. Si vuelve a pasar, "
    "escribinos a hola@ynera.com.ar y te ayudamos."
)


@app.exception_handler(StarletteHTTPException)
async def _http_exception_friendly(request: Request, exc: StarletteHTTPException):
    if exc.status_code >= 500:
        logging.exception(
            "HTTPException 5xx en %s %s: %s",
            request.method, request.url.path, exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": _FRIENDLY_5XX, "code": "internal_error"},
        )
    detail = exc.detail if exc.detail is not None else ""
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(Exception)
async def _unhandled_exception_friendly(request: Request, exc: Exception):
    logging.exception(
        "Excepcion no manejada en %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"detail": _FRIENDLY_5XX, "code": "internal_error"},
    )

# Agregar middleware de seguridad
app.add_middleware(EnhancedSecurityHeadersMiddleware)

from contextlib import asynccontextmanager

async def _migrate_add_user_cuit_column():
    """Agrega la columna `users.cuit` si aun no existe.

    `init_db()` usa `create_all(checkfirst=True)` que no modifica tablas
    existentes cuando se agrega una columna al modelo. Este helper lo cubre
    para SQLite y Postgres sin depender de Alembic.
    """
    from proyecto_maria.database.connection import engine, IS_SQLITE
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                # En SQLite preguntamos el schema con PRAGMA.
                res = await conn.exec_driver_sql("PRAGMA table_info(users)")
                cols = {row[1] for row in res.fetchall()}
                if "cuit" not in cols:
                    await conn.exec_driver_sql(
                        "ALTER TABLE users ADD COLUMN cuit VARCHAR(15)"
                    )
                    print("✅ Migracion: agregada columna users.cuit (SQLite)")
            else:
                # Postgres soporta IF NOT EXISTS directamente.
                await conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS cuit VARCHAR(15)"
                )
    except Exception as mig_err:
        print(f"⚠️ No se pudo migrar users.cuit: {mig_err}")


async def _migrate_add_user_op_defaults_columns():
    """Agrega columnas de defaults de operacion al usuario (despachante).

    Permite que cada despachante guarde su aduana/puerto/tipo destinacion
    habituales. Cuando el frontend genera el TXT MARIA, si la operacion no
    trae esos valores, se aplican estos defaults del perfil antes de caer
    al default global ARBUE/001/IC04.

    Idempotente: chequea existencia con PRAGMA (SQLite) o
    information_schema (Postgres) antes de ALTER. Si algo falla, log
    completo y RAISE: si no hay columnas, los SELECT sobre users que
    SQLAlchemy hace mas adelante van a explotar peor (500 en /api/clientes,
    /auth/current_user, etc), asi que es mejor que la app no arranque.
    """
    import traceback
    from proyecto_maria.database.connection import engine, IS_SQLITE
    new_cols = [
        ("default_aduana_codigo", "VARCHAR(10)"),
        ("default_puerto_destino", "VARCHAR(10)"),
        ("default_tipo_destinacion", "VARCHAR(10)"),
    ]
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                res = await conn.exec_driver_sql("PRAGMA table_info(users)")
                existing = {row[1] for row in res.fetchall()}
            else:
                res = await conn.exec_driver_sql(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'users'"
                )
                existing = {row[0] for row in res.fetchall()}

            for col, coltype in new_cols:
                if col in existing:
                    continue
                await conn.exec_driver_sql(
                    f"ALTER TABLE users ADD COLUMN {col} {coltype}"
                )
                print(f"✅ Migracion: agregada columna users.{col}")
    except Exception as mig_err:
        # Si fallo, NO atrapamos silenciosamente: queremos ver el stack en
        # los logs de Railway. Pero tampoco hacemos raise: prefiero que la
        # app arranque "rota" para tener un /health que devuelva diagnostico
        # antes que un container que no levanta nunca.
        print("❌ Error migrando columnas de defaults de operacion en users:")
        print(traceback.format_exc())
        print(f"❌ Error original: {mig_err!r}")


async def _migrate_add_user_billing_columns():
    """Agrega las columnas de billing (trial + PM simulado) a users.

    Idempotente, corre en cada startup. Las columnas son todas nullables
    salvo billing_status que tiene default 'none' para users existentes.
    """
    from proyecto_maria.database.connection import engine, IS_SQLITE
    new_cols = [
        ("billing_status", "VARCHAR(20) DEFAULT 'none'"),
        ("trial_ends_at", "TIMESTAMP"),
        ("payment_provider", "VARCHAR(20)"),
        ("payment_customer_id", "VARCHAR(100)"),
        ("payment_method_last4", "VARCHAR(4)"),
        ("payment_method_brand", "VARCHAR(20)"),
    ]
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                res = await conn.exec_driver_sql("PRAGMA table_info(users)")
                existing = {row[1] for row in res.fetchall()}
                for col, coltype in new_cols:
                    if col not in existing:
                        await conn.exec_driver_sql(
                            f"ALTER TABLE users ADD COLUMN {col} {coltype}"
                        )
                        print(f"✅ Migracion: agregada columna users.{col} (SQLite)")
            else:
                for col, coltype in new_cols:
                    await conn.exec_driver_sql(
                        f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {coltype}"
                    )
    except Exception as mig_err:
        print(f"⚠️ No se pudo migrar columnas de billing: {mig_err}")


async def _migrate_add_client_column_mapping():
    """Agrega `clients.column_mapping` (JSON/TEXT) si no existe.

    Idempotente. SQLite no tiene tipo JSON nativo, usamos TEXT y SQLAlchemy
    lo serializa al leer/escribir como JSON automáticamente.

    Además, si `clients.notes` contiene JSON con la forma `{__mapping: {...}}`
    (del esquema viejo), movemos el mapping al nuevo campo y restauramos notes
    a string vacío o a `__legacy_notes` si lo había.
    """
    from proyecto_maria.database.connection import engine, IS_SQLITE
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                res = await conn.exec_driver_sql("PRAGMA table_info(clients)")
                cols = {row[1] for row in res.fetchall()}
                if "column_mapping" not in cols:
                    await conn.exec_driver_sql(
                        "ALTER TABLE clients ADD COLUMN column_mapping TEXT"
                    )
                    print("✅ Migracion: agregada columna clients.column_mapping (SQLite)")
            else:
                await conn.exec_driver_sql(
                    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS column_mapping JSONB"
                )

            # Migrar notes polutos del esquema viejo
            res = await conn.exec_driver_sql(
                "SELECT id, notes, column_mapping FROM clients "
                "WHERE notes LIKE '%__mapping%'"
            )
            rows = res.fetchall()
            migrated = 0
            for row in rows:
                cid, notes_raw, existing_map = row[0], row[1], row[2]
                try:
                    blob = json.loads(notes_raw) if notes_raw else None
                except Exception:
                    blob = None
                if not isinstance(blob, dict) or "__mapping" not in blob:
                    continue
                new_mapping = blob.get("__mapping") or {}
                new_notes = blob.get("__legacy_notes") or ""
                if existing_map:
                    # ya hay mapping nuevo; solo limpiamos notes
                    cm_value = None
                else:
                    cm_value = json.dumps(new_mapping, ensure_ascii=False) if IS_SQLITE else new_mapping
                if IS_SQLITE:
                    await conn.exec_driver_sql(
                        "UPDATE clients SET notes = ?, column_mapping = COALESCE(?, column_mapping) WHERE id = ?",
                        (new_notes or None, cm_value, cid),
                    )
                else:
                    await conn.exec_driver_sql(
                        "UPDATE clients SET notes = %s, column_mapping = COALESCE(%s, column_mapping) WHERE id = %s",
                        (new_notes or None, cm_value, cid),
                    )
                migrated += 1
            if migrated:
                print(f"✅ Migracion: movidos {migrated} mappings desde clients.notes a clients.column_mapping")
    except Exception as mig_err:
        print(f"⚠️ No se pudo migrar clients.column_mapping: {mig_err}")


async def _migrate_add_client_fecha_inic_activ():
    """Agrega `clients.fecha_inic_activ` (VARCHAR(10), ISO YYYY-MM-DD) si no existe.

    Idempotente. La fecha se propaga al MARIA.TXT cuando el user fija un
    cliente activo y arma una operacion (campo comprador_fecha_inic_activ).
    """
    from proyecto_maria.database.connection import engine, IS_SQLITE
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                res = await conn.exec_driver_sql("PRAGMA table_info(clients)")
                cols = {row[1] for row in res.fetchall()}
                if "fecha_inic_activ" not in cols:
                    await conn.exec_driver_sql(
                        "ALTER TABLE clients ADD COLUMN fecha_inic_activ VARCHAR(10)"
                    )
                    print("✅ Migracion: agregada columna clients.fecha_inic_activ (SQLite)")
            else:
                await conn.exec_driver_sql(
                    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS fecha_inic_activ VARCHAR(10)"
                )
    except Exception as mig_err:
        print(f"⚠️ No se pudo migrar clients.fecha_inic_activ: {mig_err}")


async def _migrate_create_telemetry_events_table():
    """Tabla `telemetry_events` para KPIs Wave 1 (idempotente)."""
    from proyecto_maria.database.connection import engine, IS_SQLITE
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                row = (
                    await conn.exec_driver_sql(
                        "SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='telemetry_events' LIMIT 1"
                    )
                ).fetchone()
                if row:
                    return
                await conn.exec_driver_sql(
                    """
                    CREATE TABLE telemetry_events (
                        id VARCHAR(36) NOT NULL PRIMARY KEY,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        owner_username VARCHAR(50),
                        action VARCHAR(120) NOT NULL,
                        screen VARCHAR(80),
                        duration_ms INTEGER,
                        props TEXT
                    )
                    """
                )
                await conn.exec_driver_sql(
                    "CREATE INDEX ix_telemetry_created ON telemetry_events (created_at)"
                )
                print("✅ Migracion: creada tabla telemetry_events (SQLite)")
            else:
                await conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS telemetry_events (
                        id VARCHAR(36) PRIMARY KEY,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        owner_username VARCHAR(50),
                        action VARCHAR(120) NOT NULL,
                        screen VARCHAR(80),
                        duration_ms INTEGER,
                        props TEXT
                    )
                    """
                )
                await conn.exec_driver_sql(
                    "CREATE INDEX IF NOT EXISTS ix_telemetry_created ON telemetry_events (created_at)"
                )
    except Exception as mig_err:
        print(f"⚠️ No se pudo crear telemetry_events: {mig_err}")


async def _migrate_clients_email_nullable():
    """Rebuilds `clients` table if it still has the old schema (email NOT NULL
    and/or a global UNIQUE(email) constraint).

    The current model declares `email` as nullable with a per-owner uniqueness
    constraint (owner_username, email). Legacy databases created before that
    change still have the old NOT NULL + global UNIQUE, which makes it
    impossible to create clients without an email (the common case for the
    minimalist drawer that only asks razon social + CUIT + domicilio).
    """
    from proyecto_maria.database.connection import engine, IS_SQLITE
    if not IS_SQLITE:
        return
    try:
        async with engine.begin() as conn:
            info = await conn.exec_driver_sql("PRAGMA table_info(clients)")
            rows = info.fetchall()
            if not rows:
                return
            email_row = next((r for r in rows if r[1] == "email"), None)
            email_not_null = bool(email_row and email_row[3])

            idx_info = await conn.exec_driver_sql("PRAGMA index_list(clients)")
            idx_rows = idx_info.fetchall()
            has_bad_unique = False
            for idx in idx_rows:
                idx_name, is_unique = idx[1], idx[2]
                if not is_unique:
                    continue
                cols_info = await conn.exec_driver_sql(
                    f"PRAGMA index_info('{idx_name}')"
                )
                cols = [c[2] for c in cols_info.fetchall()]
                if cols == ["email"]:
                    has_bad_unique = True
                    break

            if not email_not_null and not has_bad_unique:
                return

            print("🔧 Migracion: reconstruyendo tabla clients (email nullable, unique por owner)")
            await conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
            await conn.exec_driver_sql("""
                CREATE TABLE clients_new (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    owner_username VARCHAR(50),
                    name VARCHAR(200) NOT NULL,
                    email VARCHAR(100),
                    phone VARCHAR(50),
                    cuit VARCHAR(15),
                    address TEXT,
                    notes TEXT,
                    favorite BOOLEAN DEFAULT 0,
                    default_origin VARCHAR(3) DEFAULT 'CN',
                    preferred_currency VARCHAR(3) DEFAULT 'USD',
                    auto_ncm_enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY(owner_username) REFERENCES users(username)
                )
            """)
            existing_cols = {r[1] for r in rows}
            copy_cols = [
                "id", "owner_username", "name", "email", "phone", "cuit",
                "address", "notes", "favorite", "default_origin",
                "preferred_currency", "auto_ncm_enabled", "created_at",
                "updated_at", "is_active",
            ]
            select_exprs = []
            for c in copy_cols:
                if c in existing_cols:
                    select_exprs.append(c)
                else:
                    select_exprs.append("NULL")
            await conn.exec_driver_sql(
                f"INSERT INTO clients_new ({', '.join(copy_cols)}) "
                f"SELECT {', '.join(select_exprs)} FROM clients"
            )
            await conn.exec_driver_sql("DROP TABLE clients")
            await conn.exec_driver_sql("ALTER TABLE clients_new RENAME TO clients")
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_clients_owner ON clients (owner_username)"
            )
            await conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_clients_owner_email "
                "ON clients (owner_username, email)"
            )
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
            print("✅ Migracion clients completada")
    except Exception as mig_err:
        print(f"⚠️ No se pudo migrar clients: {mig_err}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de ciclo de vida de la aplicación (Startup/Shutdown)"""
    # --- STARTUP ---
    await init_db()
    await _migrate_add_user_cuit_column()
    await _migrate_add_user_billing_columns()
    await _migrate_add_user_op_defaults_columns()
    await _migrate_clients_email_nullable()
    await _migrate_add_client_column_mapping()
    await _migrate_add_client_fecha_inic_activ()
    await _migrate_create_telemetry_events_table()
    
    # Montar Admin Router si no está montado
    # FastAPI lifespan se ejecuta antes de empezar a servir peticiones
    app.include_router(
        admin_router.router,
        dependencies=[Depends(get_current_user)]
    )
    print("🔒 Admin Router mounted with Authentication enabled.")

    async for session in get_async_session():
        try:
            from proyecto_maria.database.models import User
            
            demo_users = [
                {"username": "premium", "password": "premium123", "name": "Usuario Premium", "plan": "premium"},
                {"username": "basico", "password": "basico123", "name": "Usuario Básico", "plan": "basic"},
                {"username": "demo", "password": "demo123", "name": "Demo User", "plan": "premium"},
            ]
            
            # SECURITY: No crear demo users en producción
            if IS_PRODUCTION:
                demo_users = []
                logging.info("Skipping demo users in production")
            
            for user_data in demo_users:
                result = await session.execute(select(User).where(User.username == user_data["username"]))
                existing_user = result.scalars().first()
                
                if existing_user:
                    if existing_user.plan != user_data["plan"]:
                        existing_user.plan = user_data["plan"]
                        print(f"✅ Actualizado plan de {user_data['username']} a {user_data['plan']}")
                else:
                    hashed_pw = hash_password(user_data["password"])
                    new_user = User(
                        username=user_data["username"],
                        password=hashed_pw,
                        name=user_data["name"],
                        plan=user_data["plan"],
                        is_verified=True
                    )
                    session.add(new_user)
                    print(f"✅ Creado usuario demo: {user_data['username']} ({user_data['plan']})")
            
            await session.commit()
            print("✅ Usuarios demo verificados/creados")
        except Exception as e:
            print(f"⚠️ Error creando usuarios demo: {e}")
        break  # Solo necesitamos ejecutar esto una vez
        
    yield  # La aplicación está sirviendo peticiones
    
    # --- SHUTDOWN ---
    # Limpiar recursos si es necesario al apagar
    pass

app.router.lifespan_context = lifespan

# Modelos para password reset
class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@app.post("/auth/request-password-reset")
async def request_password_reset(request: PasswordResetRequest, req: Request, db: AsyncSession = Depends(get_db)):
    """Solicita un link de recuperación de contraseña"""
    client_ip = req.client.host
    now = datetime.now(timezone.utc).timestamp()
    
    # Rate limiting: máximo 5 intentos por IP cada 15 minutos
    if client_ip in reset_attempts:
        attempt_data = reset_attempts[client_ip]
        if attempt_data["block_until"] > now:
            wait_mins = int((attempt_data["block_until"] - now) / 60) + 1
            raise HTTPException(status_code=429, detail=f"Demasiados intentos. Intente en {wait_mins} minutos.")
    
    # Incrementar contador
    if client_ip not in reset_attempts:
        reset_attempts[client_ip] = {"count": 0, "block_until": 0}
    reset_attempts[client_ip]["count"] += 1
    
    if reset_attempts[client_ip]["count"] >= 5:
        reset_attempts[client_ip]["block_until"] = now + (15 * 60)  # 15 min
        print(f"🚫 IP {client_ip} bloqueada para reset por 15 minutos")
    
    # 1. Buscar usuario
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    
    if not user:
        # Por seguridad, no decimos si el email existe o no, pero simulamos éxito
        # Opcional: sleep aleatorio para evitar timing attacks
        return {"message": "Si el email existe, se envió un link."}

    # 2. Generar token
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # 3. Guardar token en DB
    reset_token = PasswordResetToken(
        user_username=user.username,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    await db.commit()
    
    # 4. Enviar email (o simular). El link apunta a la UI real via FRONTEND_URL.
    reset_link = f"{get_frontend_url()}/reset-password?token={token}"
    email_body = f"""
    <h1>Recuperación de Contraseña</h1>
    <p>Hola {user.name or user.username},</p>
    <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace:</p>
    <p><a href="{reset_link}">Restablecer Contraseña</a></p>
    <p>Este enlace expira en 1 hora.</p>
    <br>
    <p>Si no fuiste tú, ignora este mensaje.</p>
    """
    
    email_sent = send_email(user.email, "Recuperar Contraseña - CDI", email_body)
    
    response = {"message": "Si el email existe, se envió un link."}
    
    if not email_sent and not IS_PRODUCTION:
        # MODO DEV: Devolver token para facilitar pruebas si no hay SMTP
        print(f"🔑 [DEV] Reset Token para {user.username}: {token}")
        response["dev_token_hint"] = token
        
    return response

class RecoverUsernameRequest(BaseModel):
    email: str

@app.post("/auth/recover-username")
async def recover_username(request: RecoverUsernameRequest, db: AsyncSession = Depends(get_db)):
    """Envía el username al email del usuario"""
    # 1. Buscar usuario por email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    
    if not user:
        # Por seguridad, no revelar si el email existe
        return {"message": "Si el email está registrado, te enviamos tu nombre de usuario."}
    
    # 2. Enviar email con username
    email_body = f"""
    <h1>Tu nombre de usuario</h1>
    <p>Hola {user.name or user.username},</p>
    <p>Tu nombre de usuario es: <strong>{user.username}</strong></p>
    <p>Usá este usuario para ingresar a tu cuenta.</p>
    <br>
    <p>Si no solicitaste esto, ignorá este mensaje.</p>
    """
    
    email_sent = send_email(user.email, "Tu nombre de usuario - CDI", email_body)
    
    response = {"message": "Si el email está registrado, te enviamos tu nombre de usuario."}
    
    if not email_sent and not IS_PRODUCTION:
        # MODO DEV: Devolver username para facilitar pruebas
        print(f"🔑 [DEV] Username para {user.email}: {user.username}")
        response["dev_username_hint"] = user.username
        
    return response

@app.post("/auth/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """Restablece la contraseña usando el token"""
    # 1. Buscar token válido
    result = await db.execute(select(PasswordResetToken).where(
        PasswordResetToken.token == data.token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    ))
    reset_token = result.scalars().first()
    
    if not reset_token:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
        
    # 2. Buscar usuario
    result_user = await db.execute(select(User).where(User.username == reset_token.user_username))
    user = result_user.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # 3. Actualizar contraseña
    user.password = hash_password(data.new_password)
    
    # 4. Marcar token como usado
    reset_token.is_used = True
    
    await db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}

# --- METRICS & LOGGING ---
from starlette.middleware.base import BaseHTTPMiddleware
from proyecto_maria.database.models import APILog
from sqlalchemy import func, desc

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Procesar request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error_message = None
        except Exception as e:
            status_code = 500
            error_message = str(e)
            raise e
        finally:
            # Calcular tiempo de ejecución
            process_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Ignorar endpoints de health y estáticos para no ensuciar logs
            if request.url.path not in ["/health", "/metrics"] and not request.url.path.startswith("/static"):
                # Fire-and-forget logging (Background Task)
                # Nota: En un entorno real de alta concurrencia, esto debería ir a una cola (Redis/Celery)
                # Aquí lo hacemos directo a DB en background para simplicidad del MVP
                async def log_request_background(
                    endpoint: str, 
                    method: str, 
                    client_ip: str, 
                    status_code: int, 
                    time_ms: int,
                    error: str
                ):
                    try:
                        async for session in get_async_session():
                            log_entry = APILog(
                                endpoint=endpoint,
                                method=method,
                                client_ip=client_ip,
                                status_code=status_code,
                                response_time_ms=int(time_ms),
                                error_message=error
                            )
                            session.add(log_entry)
                            await session.commit()
                            break # Solo necesitamos una sesión
                    except Exception as e:
                        print(f"⚠️ Error logging metrics: {e}")

                # Crear tarea en background (no bloquea respuesta al usuario)
                # Usamos el loop de eventos actual
                import asyncio
                asyncio.create_task(log_request_background(
                    str(request.url.path),
                    request.method,
                    request.client.host,
                    status_code,
                    process_time,
                    error_message
                ))

        return response

app.add_middleware(MetricsMiddleware)


# --- AUTH DEPENDENCY (movido arriba para que endpoints posteriores la usen como Depends) ---
@app.get("/auth/current_user")
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Obtiene el usuario actual desde la cookie HttpOnly. Tambien se usa
    como Depends() para proteger endpoints."""
    token = request.cookies.get("access_token")

    # Fallback to Authorization header for API clients (optional)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header

    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # Trial vencido: si seguimos en 'trial' y la fecha paso, marcamos past_due.
    # No bloqueamos el request (eso sera decision del front/middleware en v2);
    # solo flaggeamos para que el dashboard pueda mostrar el banner adecuado.
    # SQLite persiste datetimes sin tz, los normalizamos a UTC-aware al comparar.
    trial_end = user.trial_ends_at
    if trial_end is not None and trial_end.tzinfo is None:
        trial_end = trial_end.replace(tzinfo=timezone.utc)
    if (
        user.billing_status == "trial"
        and trial_end is not None
        and trial_end < datetime.now(timezone.utc)
    ):
        user.billing_status = "past_due"
        try:
            await db.commit()
        except Exception:
            await db.rollback()

    return {
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "cuit": user.cuit or "",
        "plan": user.plan,
        "is_verified": user.is_verified,
        "billing_status": user.billing_status or "none",
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "default_aduana_codigo": user.default_aduana_codigo or "",
        "default_puerto_destino": user.default_puerto_destino or "",
        "default_tipo_destinacion": user.default_tipo_destinacion or "",
    }


# --- USER PROFILE ENDPOINTS ---


@app.get("/api/user/profile")
async def get_user_profile(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el perfil del usuario logueado.

    Incluye el CUIT del despachante, que se usa automaticamente como
    `cuit_agr` (CDDTAGR) al generar el MARIA.TXT si la operacion no
    sobreescribe el valor.
    """
    result = await db.execute(select(User).where(User.username == user["username"]))
    u = result.scalars().first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "success": True,
        "profile": {
            "username": u.username,
            "name": u.name or "",
            "email": u.email or "",
            "cuit": u.cuit or "",
            "plan": u.plan or "basic",
            "is_verified": bool(u.is_verified),
            "default_aduana_codigo": u.default_aduana_codigo or "",
            "default_puerto_destino": u.default_puerto_destino or "",
            "default_tipo_destinacion": u.default_tipo_destinacion or "",
        },
    }


@app.put("/api/user/profile")
async def update_user_profile(
    body: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el perfil del usuario (nombre + CUIT del despachante).

    El CUIT del despachante se guarda normalizado (solo digitos) para que
    el generador TXT lo use siempre en el mismo formato.
    """
    import re

    result = await db.execute(select(User).where(User.username == user["username"]))
    u = result.scalars().first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Name: string libre. NO escapamos en storage (el frontend escapa al renderizar);
    # asi evitamos doble-escape de '&', comillas, etc. y caracteres validos como
    # "Importadora & Hijos SRL" se guardan tal cual.
    if "name" in body:
        raw_name = body.get("name") or ""
        u.name = str(raw_name).strip()[:100] or None

    # CUIT: solo digitos, 11 chars. Permitimos limpiar con string vacio
    if "cuit" in body:
        raw_cuit = str(body.get("cuit") or "").strip()
        if raw_cuit == "":
            u.cuit = None
        else:
            digits = re.sub(r"\D", "", raw_cuit)
            if len(digits) != 11:
                raise HTTPException(
                    status_code=400,
                    detail="CUIT debe tener 11 digitos",
                )
            u.cuit = digits

    # Defaults del despachante: solo letras/numeros, max 10. Vacio = limpiar.
    def _sanitize_op_default(raw, max_len=10):
        s = str(raw or "").strip().upper()
        s = re.sub(r"[^A-Z0-9]", "", s)
        return s[:max_len] or None

    if "default_aduana_codigo" in body:
        u.default_aduana_codigo = _sanitize_op_default(body.get("default_aduana_codigo"))
    if "default_puerto_destino" in body:
        u.default_puerto_destino = _sanitize_op_default(body.get("default_puerto_destino"))
    if "default_tipo_destinacion" in body:
        u.default_tipo_destinacion = _sanitize_op_default(body.get("default_tipo_destinacion"))

    await db.commit()
    await db.refresh(u)
    return {
        "success": True,
        "profile": {
            "username": u.username,
            "name": u.name or "",
            "email": u.email or "",
            "cuit": u.cuit or "",
            "plan": u.plan or "basic",
            "is_verified": bool(u.is_verified),
            "default_aduana_codigo": u.default_aduana_codigo or "",
            "default_puerto_destino": u.default_puerto_destino or "",
            "default_tipo_destinacion": u.default_tipo_destinacion or "",
        },
    }


# --- DEV DASHBOARD ENDPOINTS ---

@app.get("/dev/dashboard")
def dev_dashboard(request: Request):
    """Panel de control para desarrolladores (Admin only)"""
    # TODO: Agregar verificación de rol admin real
    return FileResponse(os.path.join(basedir, "proyecto_maria", "templates", "dev_dashboard.html"), media_type="text/html")

@app.get("/api/dev/stats")
async def get_dev_stats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estadísticas en tiempo real para el dashboard (requiere auth).

    TODO: restringir a rol admin. Por ahora cualquier user logueado ve
    los logs agregados (no filtra por owner).
    """
    
    # 1. Total Requests (Últimas 24h)
    last_24h = datetime.now() - timedelta(hours=24)
    total_req = await db.execute(select(func.count(APILog.id)).where(APILog.created_at >= last_24h))
    total_req_count = total_req.scalar() or 0
    
    # 2. Error Rate (Últimas 24h)
    errors = await db.execute(select(func.count(APILog.id)).where(APILog.created_at >= last_24h, APILog.status_code >= 400))
    error_count = errors.scalar() or 0
    error_rate = (error_count / total_req_count * 100) if total_req_count > 0 else 0
    
    # 3. Avg Latency (Últimas 24h)
    latency = await db.execute(select(func.avg(APILog.response_time_ms)).where(APILog.created_at >= last_24h))
    avg_latency = latency.scalar() or 0
    
    # 4. Recent Logs
    logs_result = await db.execute(
        select(APILog)
        .order_by(desc(APILog.created_at))
        .limit(50)
    )
    logs = logs_result.scalars().all()
    
    return {
        "stats": {
            "total_requests_24h": total_req_count,
            "error_rate": round(error_rate, 2),
            "avg_latency_ms": int(avg_latency)
        },
        "logs": [
            {
                "time": log.created_at.strftime("%H:%M:%S"),
                "method": log.method,
                "endpoint": log.endpoint,
                "status": log.status_code,
                "latency": log.response_time_ms,
                "ip": log.client_ip
            } for log in logs
        ]
    }


@app.get("/api/dev/wave1-kpis")
async def get_dev_wave1_kpis(
    days: int = 14,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """KPIs Wave 1 sobre tabla `telemetry_events` (14 días por defecto).

    Mismo acceso que `/api/dev/stats` (usuario logueado; admin TBD).
    """
    d = max(1, min(days, 120))
    return await _wave1_compute_kpis(db, days=d)


# --- FINANCIALS & STATUS API (Quick Win) ---

@app.get("/api/dolar")
async def get_dolar():
    """Cotizaciones USD en vivo: oficial, blue, MEP. Cache 15 min."""
    from proyecto_maria.core.dolar_service import get_dolar_snapshot
    return await get_dolar_snapshot()


@app.get("/api/financials")
async def get_financials():
    """
    Cotizaciones y estado de servicios para el topbar.
    Delega al dolar_service (cache 15 min, BNA + Blue + MEP).
    """
    from proyecto_maria.core.dolar_service import get_dolar_snapshot
    snap = await get_dolar_snapshot()
    oficial = snap.get("oficial") or {}
    blue = snap.get("blue") or {}
    mep = snap.get("mep") or {}
    return {
        "dolar_bna": {
            "compra": oficial.get("compra", 0),
            "venta": oficial.get("venta", 0),
        },
        "dolar_blue": {
            "compra": blue.get("compra", 0),
            "venta": blue.get("venta", 0),
        },
        "dolar_mep": {
            "compra": mep.get("compra", 0),
            "venta": mep.get("venta", 0),
        },
        "afip_status": "online",
        "updated_at": datetime.now().strftime("%H:%M"),
        "cache": snap.get("cache"),
    }


# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=os.path.join(basedir, "proyecto_maria", "static")), name="static")

@app.get("/")
def read_root():
    """Redirige a la landing page"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "templates", "landing.html"), media_type="text/html")

@app.get("/landing_nueva")
def landing_nueva():
    """Sirve la nueva landing page para pruebas"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "templates", "landing_nueva.html"), media_type="text/html")

@app.get("/web")
def web_interface():
    """Sirve la landing page"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "templates", "landing.html"), media_type="text/html")

@app.get("/dashboard")
def dashboard(request: Request):
    """Sirve el dashboard.

    Feature flag para la beta:
      - Query `?v=1` => setea cookie cdi_ui=v1 y sirve dashboard.html (legacy).
      - Query `?v=2` => borra la cookie y sirve dashboard_v2.html (default).
      - Sino, si la cookie `cdi_ui` vale "v1" sirve v1, caso contrario v2.

    v2 queda como default. v1 es opt-in durante la transicion.
    """
    try:
        qv = (request.query_params.get("v") or "").strip()
        cookie_ui = (request.cookies.get("cdi_ui") or "").strip().lower()

        if qv == "1":
            use_v2 = False
            set_cookie = "v1"
        elif qv == "2":
            use_v2 = True
            set_cookie = "clear"
        else:
            use_v2 = (cookie_ui != "v1")
            set_cookie = None

        template_name = "dashboard_v2.html" if use_v2 else "dashboard.html"
        response = templates.TemplateResponse(
            name=template_name,
            request=request,
            context={"version": PROJECT_VERSION},
        )

        # Persistir eleccion del query param (~180 dias)
        if set_cookie == "v1":
            response.set_cookie(
                key="cdi_ui",
                value="v1",
                max_age=60 * 60 * 24 * 180,
                path="/",
                samesite="lax",
            )
        elif set_cookie == "clear":
            response.delete_cookie(key="cdi_ui", path="/")
        return response
    except Exception as e:
        print(f"Error rendering dashboard: {e}")
        return HTMLResponse(f"<h1>Error loading dashboard</h1><pre>{e}</pre>", status_code=500)


@app.post("/api/ui/event")
@app.post("/api/session/state")
async def ui_event(request: Request, db: AsyncSession = Depends(get_db)):
    """Endpoint de telemetria simple para comparar v1 vs v2 durante la beta.

    Acepta JSON (o blob sendBeacon) con: version, screen, action, duration_ms,
    ts y metadata libre. No es critico: si algo falla, no se interrumpe el flow
    del usuario. Se loggea como JSONL en `logs/ui_events.jsonl`.

    Ruta duplicada `/api/session/state` por compatibilidad con clientes legacy.

    Sin auth obligatoria para no perder eventos pre-login; el usuario opcional
    sale de Bearer o de la cookie HttpOnly de sesión cuando existe.
    """
    try:
        raw = await request.body()
        import json as _json
        payload = {}
        if raw:
            try:
                payload = _json.loads(raw.decode("utf-8"))
            except Exception:
                payload = {"raw": raw.decode("utf-8", errors="replace")[:500]}

        username = None
        auth_header = request.headers.get("authorization") or ""
        if auth_header.lower().startswith("bearer "):
            username = _jwt_sub_from_token_text(auth_header.split(" ", 1)[1])

        if not username:
            raw_cookie = request.cookies.get("access_token") or ""
            username = _jwt_sub_from_token_text(raw_cookie)

        event = {
            "ts_server": datetime.now(timezone.utc).isoformat(),
            "owner_username": username,
            "ip": request.client.host if request.client else None,
            "ua": request.headers.get("user-agent", "")[:200],
            "payload": payload,
        }

        logs_dir = os.path.join(basedir, "logs")
        try:
            os.makedirs(logs_dir, exist_ok=True)
            with open(os.path.join(logs_dir, "ui_events.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(_json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as disk_err:
            print(f"[ui_event] no se pudo escribir log: {disk_err}")

        try:
            await _persist_ui_telemetry_row(db, username, payload)
            await db.commit()
        except Exception as sql_err:
            await db.rollback()
            print(f"[ui_event] sql persist omitido: {sql_err}")

        return {"ok": True}
    except Exception as e:
        # Nunca romper la UX por un evento de telemetria
        print(f"[ui_event] error: {e}")
        return {"ok": False}

@app.get("/reset-password")
def reset_password_page():
    """Pagina dedicada para completar el reset de password.
    El link que mandamos por email apunta aca con ?token=..."""
    return FileResponse(
        os.path.join(basedir, "proyecto_maria", "templates", "reset_password.html"),
        media_type="text/html",
    )


@app.get("/estilos_landing.css")
def estilos_landing():
    """Sirve el CSS de la landing page"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "static", "estilos_landing.css"), media_type="text/css")

@app.get("/app.css")
def app_css():
    """Sirve el CSS de la aplicación"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "static", "app.css"), media_type="text/css")

@app.get("/app.js")
def app_js():
    """Sirve el JS de la aplicación"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "static", "app.js"), media_type="application/javascript")

@app.get("/app_fixed.js")
def app_fixed_js():
    """Sirve el JS fijo de la aplicación (Cache Buster)"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "static", "app_fixed.js"), media_type="application/javascript")

@app.get("/api/dev/test-clientes")
async def dev_test_clientes(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reproduce la query de /api/clientes pero atrapa cualquier error y lo
    devuelve como JSON para diagnostico. Hace los 4 pasos por separado para
    identificar cual rompe.
    """
    import traceback
    steps = []
    username = user["username"]
    try:
        steps.append({"step": "auth", "ok": True, "username": username})

        result = await db.execute(
            sa_select(ClientModel).where(
                ClientModel.owner_username == username,
                ClientModel.is_active == True,  # noqa: E712
            ).order_by(ClientModel.favorite.desc(), ClientModel.name.asc())
        )
        clients = [c for c in result.scalars().all() if c.name]
        steps.append({"step": "select_clients", "ok": True, "count": len(clients)})

        ids = [c.id for c in clients]
        if ids:
            ops_stats = await db.execute(
                sa_select(
                    OperationModel.client_id,
                    sa_func.count(OperationModel.id).label("ops_count"),
                    sa_func.sum(OperationModel.total_value).label("valor_total"),
                    sa_func.max(OperationModel.created_at).label("ultimo"),
                )
                .where(
                    OperationModel.client_id.in_(ids),
                    OperationModel.owner_username == username,
                )
                .group_by(OperationModel.client_id)
            )
            ops_rows = ops_stats.all()
            steps.append({"step": "ops_stats", "ok": True, "rows": len(ops_rows)})

            ncm_stats = await db.execute(
                sa_select(
                    ClientProductHistoryModel.client_id,
                    ClientProductHistoryModel.ncm,
                    sa_func.sum(ClientProductHistoryModel.veces_usado).label("usos"),
                )
                .where(ClientProductHistoryModel.client_id.in_(ids))
                .group_by(
                    ClientProductHistoryModel.client_id,
                    ClientProductHistoryModel.ncm,
                )
            )
            ncm_rows = ncm_stats.all()
            steps.append({"step": "ncm_stats", "ok": True, "rows": len(ncm_rows)})

        # Probar serializacion del primer cliente (puede romper aca si hay datos raros)
        if clients:
            first = clients[0]
            sample = {
                "id": first.id,
                "name": first.name,
                "cuit": first.cuit,
                "email": first.email,
                "fecha_inic_activ": getattr(first, "fecha_inic_activ", None),
                "column_mapping": getattr(first, "column_mapping", None),
            }
            steps.append({"step": "serialize_sample", "ok": True, "sample": sample})

        return {"ok": True, "steps": steps, "summary": "Todos los pasos OK"}
    except Exception as e:
        steps.append({"step": "FAILED", "ok": False, "error": repr(e)})
        return {
            "ok": False,
            "steps": steps,
            "error": repr(e),
            "traceback": traceback.format_exc(),
        }


@app.post("/api/dev/run-migrations")
async def dev_run_migrations(user=Depends(get_current_user)):
    """Re-ejecuta las migraciones idempotentes de columnas en users.

    Util cuando la migracion al startup fallo por algun motivo (lock,
    timeout, version vieja de PG sin IF NOT EXISTS) y la tabla users
    quedo desincronizada con el modelo SQLAlchemy. El resultado lista
    el output de cada migracion.
    """
    import io
    import contextlib
    buf = io.StringIO()
    results = {}
    migrations = [
        ("user_cuit", _migrate_add_user_cuit_column),
        ("user_billing", _migrate_add_user_billing_columns),
        ("user_op_defaults", _migrate_add_user_op_defaults_columns),
        ("clients_email_nullable", _migrate_clients_email_nullable),
        ("client_column_mapping", _migrate_add_client_column_mapping),
        ("client_fecha_inic_activ", _migrate_add_client_fecha_inic_activ),
        ("telemetry_events", _migrate_create_telemetry_events_table),
    ]
    for label, fn in migrations:
        try:
            with contextlib.redirect_stdout(buf):
                await fn()
            results[label] = "ok"
        except Exception as e:
            results[label] = f"error: {e!r}"
    return {
        "ok": all(v == "ok" for v in results.values()),
        "results": results,
        "log": buf.getvalue(),
    }


@app.get("/api/dev/users-schema")
async def dev_users_schema(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve las columnas existentes de la tabla users en la DB.

    Util para diagnosticar si una migracion (ej. defaults de despachante)
    corrio correctamente en produccion. Requiere auth para no exponer
    estructura interna a internet abierto.
    """
    from sqlalchemy import text
    from proyecto_maria.database.connection import IS_SQLITE
    try:
        if IS_SQLITE:
            res = await db.execute(text("PRAGMA table_info(users)"))
            cols = [{"name": row[1], "type": row[2]} for row in res.fetchall()]
        else:
            res = await db.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'users' ORDER BY ordinal_position"
                )
            )
            cols = [{"name": row[0], "type": row[1]} for row in res.fetchall()]
        col_names = {c["name"] for c in cols}
        expected_new = {
            "default_aduana_codigo",
            "default_puerto_destino",
            "default_tipo_destinacion",
        }
        missing = sorted(expected_new - col_names)
        return {
            "ok": True,
            "columns": cols,
            "missing_new_columns": missing,
            "migration_applied": not missing,
        }
    except Exception as e:
        return {"ok": False, "error": repr(e)}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Health check completo para Cloud Run - verifica API y DB"""
    from sqlalchemy import text
    checks = {
        "status": "ok",
        "api": "ok", 
        "database": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.1.0"
    }
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = "error"
        checks["status"] = "degraded"
        checks["db_error"] = str(e)[:100]
    return checks

# Configuración de hashing de contraseñas
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# Rate Limiting simple en memoria (Funciona con workers=1)
login_attempts = {} # {ip: {"count": 0, "block_until": timestamp}}
reset_attempts = {} # {ip: {"count": 0, "block_until": timestamp}} - Para reset password

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_request: LoginRequest, response: Response, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Endpoint de login con HttpOnly Cookie y Rate Limiting"""
    client_ip = request.client.host
    now = datetime.now(timezone.utc).timestamp()
    
    # Verificar bloqueo
    if client_ip in login_attempts:
        attempt_data = login_attempts[client_ip]
        if attempt_data["block_until"] > now:
            wait_seconds = int(attempt_data["block_until"] - now)
            raise HTTPException(status_code=429, detail=f"Demasiados intentos fallidos. Intente de nuevo en {wait_seconds} segundos.")
            
    username = login_request.username
    password = login_request.password
    
    # Buscar por username o por email (los usuarios nuevos se identifican
    # por email; el username se autogenera y casi nadie lo recuerda).
    result = await db.execute(
        select(User).where((User.username == username) | (User.email == username))
    )
    user = result.scalars().first()
    
    # Función auxiliar para manejar fallo y rate limit
    def handle_failed_login():
        if client_ip not in login_attempts:
            login_attempts[client_ip] = {"count": 0, "block_until": 0}
        
        login_attempts[client_ip]["count"] += 1
        
        if login_attempts[client_ip]["count"] >= 5:
            # Bloquear por 15 minutos
            login_attempts[client_ip]["block_until"] = now + (15 * 60)
            print(f"🚫 IP {client_ip} bloqueada por 15 minutos.")
            
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not user:
        handle_failed_login()
    
    stored_password = user.password
    
    # Verificar contraseña (soporta hash y texto plano legacy)
    is_valid = False
    try:
        # Intenta verificar como hash bcrypt en threadpool
        is_valid = await run_in_threadpool(verify_password, password, stored_password)
    except Exception:
        pass
        
    # Fallback para usuarios demo antiguos con contraseña plana (solo en desarrollo)
    if not is_valid and not IS_PRODUCTION and stored_password == password:
        is_valid = True
        # Migrar a hash en background para que el fallback no se necesite más
        try:
            new_hash = await run_in_threadpool(hash_password, password)
            user.password = new_hash
            await db.commit()
            print(f"🔒 Password de {username} migrada a hash bcrypt")
        except Exception:
            pass
    
    if not is_valid:
        handle_failed_login()

    # Gate de verificacion de email: si esta activado globalmente y el user
    # todavia no confirmo, bloqueamos y reenviamos el mail para que no tenga
    # que pedirlo por su cuenta.
    if _email_verification_enabled() and not user.is_verified:
        if user.email:
            background_tasks.add_task(
                send_verification_email, user.username, user.email, user.name
            )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "email_not_verified",
                "message": "Verifica tu email antes de ingresar. Te reenviamos el link de confirmacion.",
                "email": user.email,
            },
        )

    # Login exitoso: limpiar intentos fallidos
    if client_ip in login_attempts:
        del login_attempts[client_ip]
    
    token = create_access_token({"sub": username, "plan": user.plan})
    
    # Set HttpOnly Cookie (Strict CSRF Protection)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=IS_PRODUCTION,  # True en producción con HTTPS
        samesite="strict",  # Max protection against CSRF
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "message": "Login exitoso",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": username,
            "name": user.name or username,
            "plan": user.plan
        }
    }

@app.post("/auth/logout")
async def logout(response: Response):
    """Cierra sesión eliminando la cookie"""
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada"}

# ============== BACKUP/RESTORE LOCALSTORAGE ==============

@app.post("/api/backup/localStorage")
async def backup_localstorage(
    data: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persiste backup del localStorage del user autenticado."""
    from proyecto_maria.database.models import SystemBackup
    try:
        backup = SystemBackup(
            owner_username=user["username"],
            backup_type="localstorage",
            data_json=data,
        )
        db.add(backup)
        await db.commit()
        await db.refresh(backup)
        return {
            "success": True,
            "backup_id": backup.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logging.exception("backup_localstorage failed")
        return {"success": False, "error": "no se pudo guardar el backup"}


@app.get("/api/restore/localStorage")
async def restore_localstorage(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restaura el último backup de localStorage del user autenticado."""
    from proyecto_maria.database.models import SystemBackup
    try:
        result = await db.execute(
            select(SystemBackup)
            .where(
                SystemBackup.backup_type == "localstorage",
                SystemBackup.owner_username == user["username"],
            )
            .order_by(desc(SystemBackup.created_at))
            .limit(1)
        )
        backup = result.scalars().first()
        if not backup:
            return {"success": False, "error": "No hay backups disponibles"}
        return {
            "success": True,
            "data": backup.data_json,
            "backup_id": backup.id,
            "created_at": backup.created_at.isoformat() if backup.created_at else None,
        }
    except Exception as e:
        logging.exception("restore_localstorage failed")
        return {"success": False, "error": "no se pudo recuperar el backup"}

from fastapi import BackgroundTasks
from starlette.concurrency import run_in_threadpool

@app.post("/auth/register")
async def register(request: RegisterRequest, background_tasks: BackgroundTasks, response: Response, db: AsyncSession = Depends(get_db)):
    """Registro de usuario.

    Si EMAIL_VERIFICATION_REQUIRED=true (prod recomendado):
    - Usuario se crea con is_verified=False.
    - Se manda email con link a {FRONTEND_URL}/auth/verify-email?token=...
    - Igual devolvemos access_token para no bloquear (middleware mas tarde
      puede bloquear endpoints sensibles si is_verified=False).

    Si EMAIL_VERIFICATION_REQUIRED=false (default dev/beta):
    - is_verified=True de una, sin mandar email.
    """
    import re

    # Validar username (solo alfanuméricos, guiones y guiones bajos)
    if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', request.username):
        raise HTTPException(status_code=400, detail="Username inválido. Solo se permiten letras, números, guiones y guiones bajos (3-30 caracteres)")

    # Verificar si el username ya existe
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    # Verificar si el email ya existe (solo si se proporciona email)
    if request.email:
        result = await db.execute(select(User).where(User.email == request.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email ya registrado. Usa otro email o ingresa con tu cuenta existente.")

    user_name = request.name or request.username

    # Validacion temprana del metodo de pago (si vino). Si falla, 400 antes
    # de crear nada. No guardamos numero ni CVC, solo last4+brand+customer_id.
    pm_meta = None
    if request.payment_method is not None:
        from proyecto_maria.services.billing_sim import (
            validate_and_detect, CardValidationError,
        )
        try:
            pm_meta = validate_and_detect(request.payment_method.model_dump())
        except CardValidationError as ce:
            raise HTTPException(status_code=400, detail=str(ce))

    # Hash en threadpool para no bloquear el event loop (bcrypt es CPU-bound).
    hashed_password = await run_in_threadpool(hash_password, request.password)

    require_verify = _email_verification_enabled()

    new_user = User(
        username=request.username,
        password=hashed_password,
        name=user_name,
        plan=request.plan,
        email=request.email,
        is_verified=not require_verify,
    )

    # Si el user cargo tarjeta, arrancamos trial 14d con PM simulado guardado.
    if pm_meta is not None:
        new_user.billing_status = "trial"
        new_user.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=14)
        new_user.payment_provider = "simulated"
        new_user.payment_customer_id = pm_meta["customer_id"]
        new_user.payment_method_last4 = pm_meta["last4"]
        new_user.payment_method_brand = pm_meta["brand"]

    db.add(new_user)
    await db.commit()

    # Email de verificacion (solo si el toggle esta on). Lo mandamos en
    # background para no frenar el response. Pasamos strings, no el ORM,
    # porque la sesion SQLAlchemy se cierra cuando termina el request.
    if require_verify and request.email:
        background_tasks.add_task(
            send_verification_email,
            request.username,
            request.email,
            user_name,
        )

    print(
        f"Usuario registrado: {request.username} "
        f"(plan: {request.plan}, verificado: {not require_verify})"
    )

    billing_payload = {
        "billing_status": new_user.billing_status or "none",
        "trial_ends_at": new_user.trial_ends_at.isoformat() if new_user.trial_ends_at else None,
        "payment_method": (
            {"last4": new_user.payment_method_last4, "brand": new_user.payment_method_brand}
            if pm_meta is not None else None
        ),
    }

    # Gate fuerte: si se exige verificacion, NO damos acceso hasta que
    # confirme el email. Sin cookie, sin token, sin login automatico.
    # El front se encarga de mostrar la pantalla "revisa tu mail".
    if require_verify:
        return {
            "message": "Revisa tu email para confirmar tu cuenta.",
            "verification_required": True,
            "email": request.email,
            "username": request.username,
            "billing": billing_payload,
        }

    # Modo sin verificacion: devolvemos token y cookie igual que antes para
    # no frenar demos/beta (EMAIL_VERIFICATION_REQUIRED=false).
    access_token = create_access_token({
        "sub": request.username,
        "plan": request.plan,
        "roles": ["operador"],
    })

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {
        "message": "Usuario creado exitosamente",
        "verification_required": False,
        "access_token": access_token,
        "plan": request.plan,
        "roles": ["operador"],
        "billing": billing_payload,
        "username": request.username,
    }

@app.get("/auth/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Endpoint para verificar email via link enviado por mail.

    Ademas de marcar is_verified=True, loguea al user dejando la cookie
    access_token. Sin esto el user llegaba al dashboard verificado pero
    sin sesion, y todas las APIs devolvian 401 (no podia crear clientes,
    subir PDFs, nada).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "email_verification":
            raise HTTPException(status_code=400, detail="Token inválido")

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user.is_verified = True
        await db.commit()

        access_token = create_access_token({
            "sub": user.username,
            "plan": user.plan,
            "roles": ["operador"],
        })

        # Redirect a la UI real via FRONTEND_URL. En dev apunta al mismo server,
        # en prod al dominio publico del frontend.
        response = RedirectResponse(url=f"{get_frontend_url()}/dashboard?verified=true")
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="strict",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return response

    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")


@app.post("/auth/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reenvia el email de verificacion al usuario autenticado.

    Solo tiene efecto si el user todavia no esta verificado. Rate-limit
    agresivo (3/min) para evitar abuso.
    """
    result = await db.execute(select(User).where(User.username == user["username"]))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if db_user.is_verified:
        return {"message": "El email ya esta verificado", "already_verified": True}
    if not db_user.email:
        raise HTTPException(status_code=400, detail="El usuario no tiene email configurado")

    background_tasks.add_task(
        send_verification_email,
        db_user.username,
        db_user.email,
        db_user.name,
    )
    return {"message": "Email de verificacion reenviado", "email": db_user.email}


# ============== BILLING (SIMULATED) ==============

@app.get("/api/billing/me")
async def billing_me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Devuelve el estado de billing del user actual.

    Util para que el dashboard muestre trial restante, PM cargado, etc.
    """
    result = await db.execute(select(User).where(User.username == user["username"]))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "billing_status": db_user.billing_status or "none",
        "trial_ends_at": db_user.trial_ends_at.isoformat() if db_user.trial_ends_at else None,
        "payment_provider": db_user.payment_provider,
        "payment_method": (
            {
                "last4": db_user.payment_method_last4,
                "brand": db_user.payment_method_brand,
            }
            if db_user.payment_method_last4 else None
        ),
    }


@app.post("/api/billing/simulate-charge")
async def simulate_charge(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Simula un cobro exitoso: trial|past_due -> active con ciclo de 30 dias.

    No llama a ningun gateway. Sirve para demos y tests. Cuando se integre
    Stripe/MP real, este endpoint se reemplaza por el webhook de pago exitoso.
    """
    result = await db.execute(select(User).where(User.username == user["username"]))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if db_user.billing_status not in ("trial", "past_due"):
        raise HTTPException(
            status_code=409,
            detail=f"Estado de billing invalido para cobrar: {db_user.billing_status}",
        )
    if not db_user.payment_method_last4:
        raise HTTPException(
            status_code=400,
            detail="El usuario no tiene metodo de pago cargado.",
        )

    next_period_end = datetime.now(timezone.utc) + timedelta(days=30)
    db_user.billing_status = "active"
    db_user.trial_ends_at = next_period_end
    await db.commit()

    return {
        "ok": True,
        "billing_status": "active",
        "next_charge_at": next_period_end.isoformat(),
    }


@app.post("/process_operation/")
@limiter.limit(get_dynamic_rate_limit)
async def process_operation(
    request: Request,
    payload: OperationPayload,
    user=Depends(get_current_user),
):
    """
    Recibe los datos de una operación, los valida y genera el Excel.
    Requiere sesión activa (beta).
    """
    print(f"Procesando operación: {payload.operation_id}")
    
    # --- FASE 1: Validación de Datos ---
    valid_items, errors = run_pre_maria_validations(payload.items)
    
    if errors:
        print(f"Se encontraron errores de validación: {errors}")
        raise HTTPException(status_code=400, detail={"errors": errors})
        
    # --- FASE 2: Enriquecimiento con VUCE (modo mock) ---
    # Nota: el enriquecimiento completo se expone via /api/ncm/{ncm}/completo
    # Aquí solo adjuntamos licencias alertas para el response
    licencias_warnings = []
    try:
        ncms_procesados = set()
        for item in valid_items:
            ncm = str(item.pieza) if hasattr(item, 'pieza') else str(getattr(item, 'ncm', ''))
            if ncm and ncm not in ncms_procesados:
                ncms_procesados.add(ncm)
                vuce_data = get_ncm_data(ncm)
                licencias = vuce_data.get('licencias', [])
                for lic in licencias:
                    if lic.get('requerida'):
                        licencias_warnings.append({
                            'ncm': ncm,
                            'organismo': lic.get('codigo'),
                            'descripcion': lic.get('descripcion')
                        })
    except Exception as vuce_err:
        logging.warning(f"[VUCE] Error enriqueciendo items: {vuce_err}")

    # --- Generación del Excel ---
    try:
        filename = create_maria_excel(valid_items, payload.operation_id)
        print(f"Archivo generado exitosamente: {filename}")
        response_data = {
            "message": "Operación procesada y Excel generado exitosamente.",
            "filename": filename,
            "download_url": f"/download/{filename}",
            "validated_items_count": len(valid_items)
        }
        if licencias_warnings:
            response_data["vuce_warnings"] = licencias_warnings
            response_data["vuce_message"] = f"⚠️ {len(licencias_warnings)} licencia(s) requerida(s) detectadas (VUCE)"
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_max_upload_bytes() -> int:
    try:
        max_mb = float(os.getenv("MAX_UPLOAD_MB", "10"))
    except (TypeError, ValueError):
        max_mb = 10.0
    return int(max_mb * 1024 * 1024)


@app.post("/upload_excel/")
@limiter.limit(get_dynamic_rate_limit)
async def upload_excel(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    Sube un archivo Excel y lo procesa para generar un archivo en formato AVG válido.
    Requiere sesión activa.
    """
    try:
        # Validar tipo de archivo
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")

        # Leer el archivo Excel
        contents = await file.read()

        max_upload_bytes = _get_max_upload_bytes()
        if len(contents) > max_upload_bytes:
            max_mb = max_upload_bytes / 1024 / 1024
            raise HTTPException(
                status_code=413,
                detail=f"El archivo excede el tamaño máximo permitido ({max_mb:.0f} MB)"
            )
        # Sanitizar nombre de archivo (OWASP A1 - Path Traversal)
        import tempfile
        safe_name = os.path.basename(file.filename).replace('..', '_')
        temp_fd, temp_filename = tempfile.mkstemp(suffix=os.path.splitext(safe_name)[1])

        # Guardar temporalmente
        with os.fdopen(temp_fd, "wb") as f:
            f.write(contents)

        try:
            # Leer el Excel con pandas
            df = pd.read_excel(temp_filename, engine='openpyxl' if temp_filename.endswith('.xlsx') else 'xlrd')

            # Intentar extraer datos de diferentes formatos posibles
            items = extract_items_from_excel(df, file.filename)

            if not items:
                raise HTTPException(status_code=400, detail="No se pudieron extraer datos válidos del archivo Excel")

            # Generar operación ID basado en el nombre del archivo
            operation_id = file.filename.replace('.xlsx', '').replace('.xls', '').replace(' ', '_')

            # Validar items
            valid_items, errors = run_pre_maria_validations(items)

            if errors:
                raise HTTPException(status_code=400, detail={"errors": errors, "items_extraidos": len(items)})

            # Generar Excel en formato AVG
            filename = create_maria_excel(valid_items, operation_id)

            return {
                "message": "Archivo Excel procesado exitosamente",
                "filename": filename,
                "items_procesados": len(valid_items),
                "items_extraidos": len(items)
            }

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="El archivo Excel está vacío")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


@app.post("/upload_excel/public")
@limiter.limit(get_dynamic_rate_limit)
async def upload_excel_public(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """Alias legacy de /upload_excel/. Mantiene el path 'public' solo para
    compatibilidad con el frontend actual, pero YA requiere auth."""
    return await upload_excel(request, file, user)


@app.post("/api/validate/smart")
async def smart_validation(body: dict, user=Depends(get_current_user)):
    """
    🧠 VALIDACIÓN INTELIGENTE PREMIUM
    
    Analiza items antes de generar Excel y detecta:
    - Peso sospechoso para el tipo de producto
    - Valor unitario fuera de rango típico  
    - NCM que requieren permisos especiales (ANMAT, ENACOM)
    - Descripciones muy cortas
    - Relación valor/peso sospechosa
    
    Returns:
        - errores: Problemas críticos
        - advertencias: Revisar pero puede continuar
        - sugerencias: Mejoras opcionales
        - estadisticas: Resumen numérico
    """
    try:
        items_data = body.get("items", [])
        if not items_data:
            return {"success": False, "detail": "No hay items para validar"}
        
        # Convertir a objetos Item
        items = []
        for item_dict in items_data:
            try:
                items.append(Item(**item_dict))
            except Exception as e:
                # Si falla la conversión, crear Item con valores por defecto
                items.append(Item(
                    pieza=item_dict.get("pieza", ""),
                    descripcion=item_dict.get("descripcion", ""),
                    origen=item_dict.get("origen", "XX"),
                    cantidad=float(item_dict.get("cantidad", 1)),
                    valor_unitario=float(item_dict.get("valor_unitario", 0)),
                    peso_unitario=float(item_dict.get("peso_unitario", 0))
                ))
        
        # Ejecutar validación inteligente
        resultado = run_smart_validations(items)
        
        return {
            "success": True,
            **resultado
        }
        
    except Exception as e:
        return {"success": False, "detail": str(e)}

@app.post("/upload_pdf/public")
@limiter.limit(get_dynamic_rate_limit)
async def upload_pdf_public(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    Sube y procesa un archivo PDF para extraer items y datos de operación.
    Requiere sesión activa (Gemini Vision consume créditos).
    """
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

        contents = await file.read()
        
        max_upload_bytes = _get_max_upload_bytes()
        if len(contents) > max_upload_bytes:
            max_mb = max_upload_bytes / 1024 / 1024
            raise HTTPException(
                status_code=413,
                detail=f"El archivo PDF excede el tamaño máximo permitido ({max_mb:.0f} MB)"
            )
            
        # Procesar PDF con el extractor
        print(f"Procesando PDF: {file.filename} ({len(contents)} bytes)")
        result = process_pdf(contents)
        
        # Manejar tanto formato nuevo (dict) como viejo (lista)
        if isinstance(result, dict) and 'items' in result:
            # Nuevo formato con operacion + items
            items_data = result.get('items', [])
            operacion_data = result.get('operacion', {})
        elif isinstance(result, list):
            # Formato viejo: solo lista de items
            items_data = result
            operacion_data = {}
        else:
            items_data = []
            operacion_data = {}

        # Fallback heurístico: si Vision no detectó vendedor (path no-LLM o
        # respuesta incompleta), intentar extraerlo del texto crudo del PDF.
        # Falla silenciosa: solo es una mejora opcional.
        if not operacion_data.get('vendedor_nombre'):
            try:
                from proyecto_maria.pdf_extractor import (
                    _extract_pdf_text,
                    detect_vendor_from_text,
                )
                pdf_text = _extract_pdf_text(contents)
                detected = detect_vendor_from_text(pdf_text)
                if detected:
                    operacion_data['vendedor_nombre'] = detected
                    operacion_data['vendedor_detectado_heuristica'] = True
            except Exception as e:
                logging.debug(f"vendor heuristic detection failed: {e}")

        if not items_data:
             raise HTTPException(status_code=400, detail="No se encontró tabla de items en el PDF. Asegurate de que el PDF tenga una tabla con columnas como: Model/Description, Price, Quantity.")

        return {
            "message": "PDF procesado exitosamente",
            "filename": file.filename,
            "operacion": operacion_data,  # Datos de la operación extraídos
            "items": items_data,  # Items extraídos
            "items_count": len(items_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error procesando PDF (upload_pdf_public)")
        raise HTTPException(
            status_code=500,
            detail="No pudimos procesar el PDF. Probá con otro archivo o escribinos a hola@ynera.com.ar y te ayudamos.",
        )


class MariaRequest(BaseModel):
    """Request para generar archivo MARIA TXT."""
    operation_id: str
    items: list
    moneda: str = "DOL"
    incoterm: str = "FOB"
    cuit_agr: str = ""
    vendedor_nombre: str = ""
    vendedor_id: str = ""
    comprador_nombre: str = ""
    comprador_cuit: str = ""
    # Datos del importador que antes se hardcodeaban en el TXT. Si vienen
    # vacios se mantiene el fallback historico para no romper operaciones
    # ya existentes.
    comprador_domicilio: str = ""
    comprador_fecha_inic_activ: str = ""
    flete: float = 0
    seguro: float = 0
    # Transport data
    bl_numero: str = ""
    puerto_origen: str = ""
    puerto_destino: str = "ARBUE"
    buque_nombre: str = ""
    viaje_numero: str = ""
    fecha_embarque: str = ""
    # Factura (antes se hardcodeaba a hoy, bug reportado)
    fecha_emision: str = ""
    # Container data
    contenedor_numero: str = ""
    contenedor_tipo: str = ""
    contenedor_peso: float = 0
    # Aduana / tipo destinacion (antes hardcodeado a 001 / IC04)
    aduana_codigo: str = "001"
    tipo_destinacion: str = "IC04"


@app.post("/generate_maria")
async def generate_maria_endpoint(
    request: MariaRequest,
    user=Depends(get_current_user),
):
    """
    Genera archivo TXT en formato MARIA para el sistema SIM de AFIP.
    Requiere sesión activa.
    
    Recibe los items con: ncm/pieza, cantidad, valor_unitario, peso_kg, origen
    Devuelve: archivo TXT descargable
    """
    try:
        # Validar items
        valid, errors = validate_items_for_maria(request.items)
        if not valid:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        # Si el user tiene CUIT en su perfil y la request no manda cuit_agr,
        # usamos el del perfil (para que el despachante no tenga que re-escribir
        # su propio CUIT en cada operacion).
        effective_cuit_agr = request.cuit_agr
        try:
            if not effective_cuit_agr and user and user.get("cuit"):
                effective_cuit_agr = str(user["cuit"]).strip()
        except Exception:
            pass

        # Generar TXT
        txt_content = generate_maria_txt(
            operation_id=request.operation_id,
            items=request.items,
            moneda=request.moneda,
            incoterm=request.incoterm,
            cuit_agr=effective_cuit_agr,
            vendedor_nombre=request.vendedor_nombre,
            vendedor_id=request.vendedor_id,
            comprador_nombre=request.comprador_nombre,
            comprador_cuit=request.comprador_cuit,
            comprador_domicilio=request.comprador_domicilio,
            comprador_fecha_inic_activ=request.comprador_fecha_inic_activ,
            flete=request.flete,
            seguro=request.seguro,
            bl_numero=request.bl_numero,
            puerto_origen=request.puerto_origen,
            puerto_destino=request.puerto_destino,
            buque_nombre=request.buque_nombre,
            viaje_numero=request.viaje_numero,
            fecha_embarque=request.fecha_embarque,
            fecha_emision=request.fecha_emision,
            contenedor_numero=request.contenedor_numero,
            contenedor_tipo=request.contenedor_tipo,
            contenedor_peso=request.contenedor_peso,
            aduana_codigo=request.aduana_codigo,
            tipo_destinacion=request.tipo_destinacion,
        )
        
        # Sanitizar operation_id para filename (prevenir path traversal)
        import re
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', request.operation_id)[:50]
        if not safe_id:
            safe_id = f"OP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Guardar archivo temporal
        filename = f"MARIA_{safe_id}.TXT"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return {
            "success": True,
            "filename": filename,
            "download_url": f"/download/{filename}",
            "content": txt_content  # También devolver contenido para preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generando MARIA TXT: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando archivo MARIA: {str(e)}")


# === EXPORT MARIA TXT ===
class MariaExportRequest(BaseModel):
    operation_id: str
    items: list
    moneda: str = "DOL"
    incoterm: str = "FOB"
    cuit_exportador: str = ""
    exportador_nombre: str = ""
    comprador_nombre: str = ""
    comprador_pais: str = "US"
    comprador_id: str = ""
    flete: float = 0
    seguro: float = 0
    tipo_destinacion: str = "EC01"
    aduana_salida: str = "001"
    medio_transporte: str = "01"


@app.post("/generate_maria_export")
async def generate_maria_export_endpoint(
    request: MariaExportRequest,
    user=Depends(get_current_user),
):
    """
    Genera archivo TXT en formato MARIA para EXPORTACIÓN.
    Requiere sesión activa.
    
    Similar a /generate_maria pero para destinaciones de exportación.
    """
    try:
        from proyecto_maria.core.maria_generator_export import (
            generate_maria_export_txt,
            validate_items_for_export,
        )
        
        # Validar items
        valid, errors = validate_items_for_export(request.items)
        if not valid:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        # Generar TXT
        txt_content = generate_maria_export_txt(
            operation_id=request.operation_id,
            items=request.items,
            moneda=request.moneda,
            incoterm=request.incoterm,
            cuit_exportador=request.cuit_exportador,
            exportador_nombre=request.exportador_nombre,
            comprador_nombre=request.comprador_nombre,
            comprador_pais=request.comprador_pais,
            comprador_id=request.comprador_id,
            flete=request.flete,
            seguro=request.seguro,
            tipo_destinacion=request.tipo_destinacion,
            aduana_salida=request.aduana_salida,
            medio_transporte=request.medio_transporte,
        )
        
        # Sanitizar operation_id para filename
        import re
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', request.operation_id)[:50]
        if not safe_id:
            safe_id = f"EXP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Guardar archivo temporal
        filename = f"MARIA_EXPORT_{safe_id}.TXT"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return {
            "success": True,
            "tipo": "exportacion",
            "filename": filename,
            "download_url": f"/download/{filename}",
            "content": txt_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generando MARIA EXPORT TXT: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando archivo MARIA export: {str(e)}")

def extract_items_from_excel(df: pd.DataFrame, filename: str) -> list[Item]:
    """
    Extrae items de un DataFrame de Excel intentando diferentes formatos.
    """
    items = []

    # Intentar diferentes formatos/mapeos de columnas
    possible_mappings = [
        # Formato AVG actual
        {
            'pieza': ['pieza', 'Pieza', 'pieza', 'ncm', 'NCM', 'codigo', 'Código'],
            'descripcion': ['descripcion', 'Descripcion', 'descripción', 'Descripción', 'desc', 'Desc'],
            'origen': ['origen', 'Origen', 'pais', 'País', 'country', 'Country'],
            'peso_unitario': ['peso_unitario', 'Peso Unitario', 'peso', 'Peso', 'weight', 'Weight'],
            'cantidad': ['cantidad', 'Cantidad', 'qty', 'Qty', 'quantity', 'Quantity'],
            'valor_unitario': ['valor_unitario', 'Valor Unitario', 'valor', 'Valor', 'price', 'Price', 'unit_price']
        },
        # Formato simple
        {
            'pieza': ['pieza', 'codigo', 'ncm'],
            'descripcion': ['descripcion', 'desc'],
            'origen': ['origen', 'pais'],
            'peso_unitario': ['peso', 'peso_unitario'],
            'cantidad': ['cantidad', 'cant'],
            'valor_unitario': ['valor', 'precio', 'valor_unitario']
        }
    ]

    for mapping in possible_mappings:
        items = try_extract_with_mapping(df, mapping)
        if items:
            print(f"✅ Extraídos {len(items)} items usando mapeo: {list(mapping.keys())}")
            break

    return items

def try_extract_with_mapping(df: pd.DataFrame, mapping: dict) -> list[Item]:
    """
    Intenta extraer items usando un mapeo específico de columnas.
    """
    items = []

    for _, row in df.iterrows():
        try:
            # Buscar columnas que coincidan con el mapeo
            pieza_col = find_column(df.columns, mapping['pieza'])
            desc_col = find_column(df.columns, mapping['descripcion'])
            origen_col = find_column(df.columns, mapping['origen'])
            peso_col = find_column(df.columns, mapping['peso_unitario'])
            cant_col = find_column(df.columns, mapping['cantidad'])
            valor_col = find_column(df.columns, mapping['valor_unitario'])

            # Si no encuentra todas las columnas obligatorias, continuar con otro mapeo
            if not all([pieza_col, desc_col, origen_col, peso_col, cant_col, valor_col]):
                continue

            # Extraer valores
            pieza = str(row[pieza_col]).strip() if pd.notna(row[pieza_col]) else ""
            descripcion = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else ""
            origen = str(row[origen_col]).strip() if pd.notna(row[origen_col]) else ""

            try:
                peso_unitario = float(row[peso_col]) if pd.notna(row[peso_col]) else 0
                cantidad = float(row[cant_col]) if pd.notna(row[cant_col]) else 0
                valor_unitario = float(row[valor_col]) if pd.notna(row[valor_col]) else 0
            except (ValueError, TypeError):
                continue  # Saltar fila si no puede convertir números

            # Solo agregar si tiene datos básicos
            if pieza and descripcion and origen and peso_unitario > 0 and cantidad > 0 and valor_unitario > 0:
                item = Item(
                    pieza=pieza,
                    descripcion=descripcion,
                    origen=origen,
                    peso_unitario=peso_unitario,
                    cantidad=cantidad,
                    valor_unitario=valor_unitario
                )
                items.append(item)

        except Exception as e:
            print(f"⚠️  Error procesando fila: {e}")
            continue

    return items

def find_column(columns, possible_names):
    """
    Busca una columna que coincida con alguno de los nombres posibles.
    """
    columns_lower = [str(col).lower().strip() for col in columns]

    for name in possible_names:
        name_lower = name.lower().strip()
        if name_lower in columns_lower:
            index = columns_lower.index(name_lower)
            return columns[index]

    return None

@app.get("/download/{filename}")
async def download_file(filename: str, user=Depends(get_current_user)):
    """
    Descarga un archivo generado (Excel o TXT). Requiere autenticación.
    """
    # Path traversal protection
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(DATA_DIR, safe_filename)
    
    # Verify file is within DATA_DIR
    if not os.path.realpath(file_path).startswith(os.path.realpath(DATA_DIR)):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if filename.lower().endswith('.txt'):
        media_type = "text/plain"
        
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
    )

# --- Endpoints de Clientes y Backup (MULTI-TENANT) ---
# Todos los endpoints requieren auth y filtran por owner_username.
# Los paths `/public/*` se conservan por compatibilidad con el frontend
# actual, pero YA NO son públicos: requieren sesión igual que el resto.

from proyecto_maria.database.models import (
    Client as ClientModel,
    Operation as OperationModel,
    OperationItem as OperationItemModel,
    NCMNote as NCMNoteModel,
    ClientProductHistory as ClientProductHistoryModel,
)
from sqlalchemy import delete as sa_delete, select as sa_select, func as sa_func, desc as sa_desc


def _client_to_dict(c: ClientModel) -> dict:
    """Serializa un Client a la forma que espera el frontend legacy + campos extras v2."""
    return {
        "id": c.id,
        "nombre": c.name,
        "email": c.email or "",
        "telefono": c.phone or "",
        "cuit": c.cuit or "",
        "direccion": c.address or "",
        "notas": c.notes or "",
        "favorito": bool(c.favorite),
        "default_origin": c.default_origin or "",
        "preferred_currency": c.preferred_currency or "",
        "auto_ncm_enabled": bool(c.auto_ncm_enabled) if c.auto_ncm_enabled is not None else True,
        "fecha_inic_activ": c.fecha_inic_activ or "",
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _digits_only(raw: str | None, maxlen: int = 20) -> str:
    return "".join(ch for ch in (raw or "") if ch.isdigit())[:maxlen]


def _jwt_sub_from_token_text(raw: str) -> str | None:
    tok = raw.strip()
    if tok.startswith("Bearer "):
        tok = tok[7:].strip()
    if not tok:
        return None
    try:
        decoded = jwt.decode(tok, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded.get("sub")
    except Exception:
        return None


async def _persist_ui_telemetry_row(db: AsyncSession, owner_username: str | None, payload: dict) -> None:
    """Insert en `telemetry_events` (no bloquear la UX ante fallos de DB)."""
    from sqlalchemy import text as sa_text

    pid = str(uuid.uuid4())
    action = str(payload.get("action") or "").strip()[:120] or "unknown"
    screen_raw = payload.get("screen")
    screen_val = (
        str(screen_raw).strip()[:80] if screen_raw is not None else None
    ) or None
    dur_raw = payload.get("duration_ms")
    try:
        duration_ms = int(dur_raw) if dur_raw is not None else None
    except (TypeError, ValueError):
        duration_ms = None
    thin = {
        k: v
        for k, v in payload.items()
        if k not in ("action", "screen", "duration_ms")
    }
    props_txt = json.dumps(thin, ensure_ascii=False)[:8000]

    await db.execute(
        sa_text(
            "INSERT INTO telemetry_events "
            "(id, owner_username, action, screen, duration_ms, props) "
            "VALUES (:id, :owner_username, :action, :screen, :duration_ms, :props)"
        ),
        {
            "id": pid,
            "owner_username": owner_username,
            "action": action,
            "screen": screen_val,
            "duration_ms": duration_ms,
            "props": props_txt,
        },
    )


def _parse_telemetry_created_at(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    s = str(val).strip()
    try:
        if "T" in s:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _median_nums(nums: list) -> float | None:
    if not nums:
        return None
    srt = sorted(nums)
    n = len(srt)
    m = n // 2
    if n % 2:
        return float(srt[m])
    return (srt[m - 1] + srt[m]) / 2


async def _wave1_db_activation_counts(db: AsyncSession, cutoff_utc: datetime) -> dict:
    """Cuentas de altas nuevas por created_at (`users`). Independiente del tracking UI."""
    from sqlalchemy import func as sa_func, select as sa_sel

    try:
        stmt_new = sa_sel(sa_func.count()).select_from(User).where(User.created_at >= cutoff_utc)
        stmt_verified = (
            sa_sel(sa_func.count())
            .select_from(User)
            .where(User.created_at >= cutoff_utc, User.is_verified.is_(True))
        )
        cn = (await db.execute(stmt_new)).scalar_one()
        cv = (await db.execute(stmt_verified)).scalar_one()
        return {
            "new_accounts_in_window": int(cn or 0),
            "new_accounts_verified_in_window": int(cv or 0),
        }
    except Exception as db_err:
        return {
            "new_accounts_in_window": None,
            "new_accounts_verified_in_window": None,
            "error": str(db_err)[:120],
        }


async def _wave1_compute_kpis(db: AsyncSession, days: int = 14) -> dict:
    from sqlalchemy import text as sa_text
    from proyecto_maria.database.connection import IS_SQLITE

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    db_window = await _wave1_db_activation_counts(db, cutoff)
    try:
        if IS_SQLITE:
            cutoff_sql = cutoff.strftime("%Y-%m-%d %H:%M:%S")
            stmt = sa_text(
                "SELECT owner_username, action, duration_ms, props, created_at "
                "FROM telemetry_events "
                "WHERE datetime(created_at) >= datetime(:cutoff)"
            )
            res = await db.execute(stmt, {"cutoff": cutoff_sql})
        else:
            stmt = sa_text(
                "SELECT owner_username, action, duration_ms, props, created_at "
                "FROM telemetry_events WHERE created_at >= :cutoff"
            )
            res = await db.execute(stmt, {"cutoff": cutoff})
        rows = list(res.mappings().all())
    except Exception as sql_err:
        print(f"[wave1-kpis] read error: {sql_err}")
        return {
            "days": days,
            "telemetry_rows_sampled": 0,
            "error": str(sql_err)[:160],
            "distinct_logged_users": 0,
            "counts": {},
            "activation": {
                "telemetry_read_failed": True,
                "database_window_accounts": db_window,
                "documentation": {
                    "definitions": "docs/wave1_activation_definitions.md",
                    "interview_kit": "docs/wave1_interview_kit.md",
                    "phase2_gate": "docs/wave1_phase2_gate.md",
                },
            },
        }

    actions_count: dict[str, int] = {}
    users_by_action: dict[str, set[str]] = {}
    per_user_pdf_ts: dict[str, list[float]] = {}
    per_user_sess_ts: dict[str, list[float]] = {}
    for row in rows:
        act = row["action"]
        actions_count[act] = actions_count.get(act, 0) + 1
        user = row["owner_username"]
        if not user:
            continue
        u = str(user)
        users_by_action.setdefault(act, set()).add(u)
        ts = _parse_telemetry_created_at(row["created_at"])
        if ts is None:
            continue
        if ts < cutoff:
            continue
        if act == "pdf_uploaded":
            per_user_pdf_ts.setdefault(u, []).append(ts.timestamp())
        if act == "session_start":
            per_user_sess_ts.setdefault(u, []).append(ts.timestamp())

    deltas = []
    for u, pdf_ts_list in per_user_pdf_ts.items():
        sess_ts_list = per_user_sess_ts.get(u)
        if not sess_ts_list:
            continue
        pdf_min = min(pdf_ts_list)
        sess_min = min(sess_ts_list)
        d = pdf_min - sess_min
        if d >= 0 and d <= 86400 * days:
            deltas.append(d)

    denom_sim = actions_count.get("pdf_uploaded", 0) + actions_count.get("upload_simulated", 0)

    demo_ratio_pct = round(
        100 * actions_count.get("upload_simulated", 0) / denom_sim, 2
    ) if denom_sim else None

    def _uniq_logged(action: str) -> int:
        return len(users_by_action.get(action, set()))

    activation = {
        "documentation": {
            "definitions_md": "docs/wave1_activation_definitions.md",
            "interview_kit_md": "docs/wave1_interview_kit.md",
            "phase2_gate_md": "docs/wave1_phase2_gate.md",
        },
        "unique_logged_users_by_action": {
            "session_start": _uniq_logged("session_start"),
            "login_completed": _uniq_logged("login_completed"),
            "register_completed": _uniq_logged("register_completed"),
            "pdf_uploaded": _uniq_logged("pdf_uploaded"),
            "upload_simulated": _uniq_logged("upload_simulated"),
            "review_confirmed": _uniq_logged("review_confirmed"),
            "maria_generated": _uniq_logged("maria_generated"),
        },
        "event_counts_no_unique_logged_user_typical": {
            "register_pending_verify": actions_count.get("register_pending_verify", 0),
        },
        "database_window_accounts": db_window,
        "recommended_shortcuts_for_pm_reports": (
            "Valor tangible: unique_logged_users_by_action.maria_generated · "
            "Intención documento real: pdf_uploaded · Cuentas nuevas (DB): "
            "database_window_accounts.new_accounts_in_window"
        ),
    }

    return {
        "days": days,
        "telemetry_rows_sampled": len(rows),
        "distinct_logged_users": len(
            {r["owner_username"] for r in rows if r["owner_username"]}
        ),
        "counts": dict(sorted(actions_count.items(), key=lambda kv: (-kv[1], kv[0]))),
        "median_sec_session_start_to_pdf": _median_nums(deltas),
        "demo_share_pct_of_demo_plus_pdf": demo_ratio_pct,
        "auto_detect_pdf_hits": actions_count.get("importador_auto_detected", 0),
        "auto_detect_misses": actions_count.get("importador_no_match", 0),
        "activation": activation,
        "activation_aliases_for_dashboard": {
            "users_maria_generated": _uniq_logged("maria_generated"),
            "users_pdf_uploaded": _uniq_logged("pdf_uploaded"),
            "users_registered_session": _uniq_logged("register_completed"),
            "users_login_session": _uniq_logged("login_completed"),
        },
    }


async def _get_owned_client(
    db: AsyncSession, client_id: str, username: str
) -> ClientModel:
    """Devuelve el Client si pertenece al user, sino 404.

    Usamos 404 (no 403) para no filtrar la existencia de recursos ajenos.
    """
    result = await db.execute(
        sa_select(ClientModel).where(
            ClientModel.id == client_id,
            ClientModel.owner_username == username,
        )
    )
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@app.get("/api/clientes")
@app.get("/api/clientes/public")  # alias legacy; ahora requiere auth
async def list_clientes(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista los clientes del usuario autenticado con resumen inline.

    Incluye por cliente: ops_count, valor_total, ultimo (ISO date string)
    y ncm_top. Se calcula en 2 queries agregadas para evitar N+1 al abrir
    el drawer en v2.
    """
    username = user["username"]
    result = await db.execute(
        sa_select(ClientModel)
        .where(
            ClientModel.owner_username == username,
            ClientModel.is_active == True,  # noqa: E712
        )
        .order_by(ClientModel.favorite.desc(), ClientModel.name.asc())
    )
    clients = [c for c in result.scalars().all() if c.name]

    resumen: dict[str, dict] = {}
    if clients:
        ids = [c.id for c in clients]

        ops_stats = await db.execute(
            sa_select(
                OperationModel.client_id,
                sa_func.count(OperationModel.id).label("ops_count"),
                sa_func.sum(OperationModel.total_value).label("valor_total"),
                sa_func.max(OperationModel.created_at).label("ultimo"),
            )
            .where(
                OperationModel.client_id.in_(ids),
                OperationModel.owner_username == username,
            )
            .group_by(OperationModel.client_id)
        )
        for row in ops_stats.all():
            resumen[row.client_id] = {
                "ops_count": int(row.ops_count or 0),
                "valor_total": float(row.valor_total or 0),
                "ultimo": row.ultimo.isoformat() if row.ultimo else None,
                "ncm_top": None,
            }

        ncm_stats = await db.execute(
            sa_select(
                ClientProductHistoryModel.client_id,
                ClientProductHistoryModel.ncm,
                sa_func.sum(ClientProductHistoryModel.veces_usado).label("usos"),
            )
            .where(ClientProductHistoryModel.client_id.in_(ids))
            .group_by(
                ClientProductHistoryModel.client_id,
                ClientProductHistoryModel.ncm,
            )
        )
        top_por_cliente: dict[str, tuple[str, int]] = {}
        for row in ncm_stats.all():
            current = top_por_cliente.get(row.client_id)
            usos = int(row.usos or 0)
            if not current or usos > current[1]:
                top_por_cliente[row.client_id] = (row.ncm, usos)
        for cid, (ncm_top, _usos) in top_por_cliente.items():
            resumen.setdefault(
                cid,
                {"ops_count": 0, "valor_total": 0.0, "ultimo": None, "ncm_top": None},
            )["ncm_top"] = ncm_top

    def _with_resumen(c: ClientModel) -> dict:
        data = _client_to_dict(c)
        r = resumen.get(c.id, {
            "ops_count": 0,
            "valor_total": 0.0,
            "ultimo": None,
            "ncm_top": None,
        })
        data["ops_count"] = r["ops_count"]
        data["valor_total"] = r["valor_total"]
        data["ultimo"] = r["ultimo"]
        data["ncm_top"] = r["ncm_top"]
        return data

    return {
        "success": True,
        "clientes": [_with_resumen(c) for c in clients],
    }


@app.get("/api/clientes/by-cuit/{cuit}")
async def get_cliente_por_cuit(
    cuit: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Busca cliente del despachante que coincida con el CUIT (solo dígitos)."""
    username = user["username"]
    needle = _digits_only(cuit, 15)
    if len(needle) < 11:
        raise HTTPException(status_code=400, detail="CUIT inválido")
    needle = needle[:11]
    result = await db.execute(
        sa_select(ClientModel).where(
            ClientModel.owner_username == username,
            ClientModel.is_active == True,  # noqa: E712
        )
    )
    for row in result.scalars().all():
        cand = _digits_only(row.cuit, 15)
        cand = cand[:11] if len(cand) >= 11 else cand
        if cand == needle:
            return {"success": True, "match": "exact", "cliente": _client_to_dict(row)}
    return {"success": True, "match": "none"}


@app.post("/api/clientes")
@app.post("/api/clientes/public")
async def create_cliente(
    client: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crea un cliente asociado al usuario autenticado.

    No aplicamos html.escape() al guardar: el frontend escapa al renderizar y
    asi evitamos doble-escape ('Importadora & Hijos' guardado como
    'Importadora &amp; Hijos'). Truncamos a los limites de las columnas para
    no devolver 500s feos cuando el user pega un string largo.
    """
    username = user["username"]
    nombre = str(client.get("nombre", "")).strip()[:200]
    email = str(client.get("email", "")).strip()[:100]
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre requerido")

    # Evitar duplicados por (owner, email) si se provee email.
    if email:
        existing = await db.execute(
            sa_select(ClientModel).where(
                ClientModel.owner_username == username,
                ClientModel.email == email,
                ClientModel.is_active == True,  # noqa: E712
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=409,
                detail=f"Ya tenés un cliente con el email {email}",
            )

    default_origin = str(client.get("default_origin", "")).strip().upper()[:3] or None
    preferred_currency = str(client.get("preferred_currency", "")).strip().upper()[:3] or None
    auto_ncm_enabled = client.get("auto_ncm_enabled")
    if auto_ncm_enabled is None:
        auto_ncm_enabled = True

    fecha_inic_activ = str(client.get("fecha_inic_activ", "")).strip()[:10] or None

    new_client = ClientModel(
        id=str(uuid.uuid4()),
        owner_username=username,
        name=nombre,
        email=email or None,
        phone=str(client.get("telefono", "")).strip()[:50] or None,
        cuit=str(client.get("cuit", "")).strip()[:15] or None,
        address=str(client.get("direccion", "")).strip() or None,
        notes=str(client.get("notas", "")).strip() or None,
        favorite=bool(client.get("favorito", False)),
        default_origin=default_origin,
        preferred_currency=preferred_currency,
        auto_ncm_enabled=bool(auto_ncm_enabled),
        fecha_inic_activ=fecha_inic_activ,
        is_active=True,
    )
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return {"success": True, "cliente": _client_to_dict(new_client)}


@app.put("/api/clientes/{client_id}")
@app.put("/api/clientes/public/{client_id}")
async def update_cliente(
    client_id: str,
    client_data: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un cliente propio del usuario autenticado.

    Sin html.escape() en storage (ver create_cliente). Truncamos al limite de
    cada VARCHAR para evitar 500s sobre input largo.
    """
    username = user["username"]
    client = await _get_owned_client(db, client_id, username)

    if "nombre" in client_data:
        client.name = str(client_data["nombre"]).strip()[:200]
    if "email" in client_data:
        client.email = str(client_data["email"] or "").strip()[:100] or None
    if "telefono" in client_data:
        client.phone = str(client_data.get("telefono", "")).strip()[:50] or None
    if "direccion" in client_data:
        client.address = str(client_data.get("direccion", "")).strip() or None
    if "notas" in client_data:
        client.notes = str(client_data.get("notas", "")).strip() or None
    if "cuit" in client_data:
        client.cuit = str(client_data.get("cuit", "")).strip()[:15] or None
    if "favorito" in client_data:
        client.favorite = bool(client_data.get("favorito"))
    if "default_origin" in client_data:
        val = str(client_data.get("default_origin", "")).strip().upper()[:3]
        client.default_origin = val or None
    if "preferred_currency" in client_data:
        val = str(client_data.get("preferred_currency", "")).strip().upper()[:3]
        client.preferred_currency = val or None
    if "auto_ncm_enabled" in client_data:
        client.auto_ncm_enabled = bool(client_data.get("auto_ncm_enabled"))
    if "fecha_inic_activ" in client_data:
        val = str(client_data.get("fecha_inic_activ", "") or "").strip()[:10]
        client.fecha_inic_activ = val or None
    await db.commit()
    await db.refresh(client)
    return {"success": True, "cliente": _client_to_dict(client)}


@app.get("/api/clients/{client_id}")  # alias histórico (EN)
@app.get("/api/clientes/{client_id}")
async def get_cliente(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detalle de un cliente propio."""
    client = await _get_owned_client(db, client_id, user["username"])
    return _client_to_dict(client)


@app.post("/api/clientes/{client_id}/favorito")
async def toggle_favorito(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca/desmarca un cliente como favorito."""
    client = await _get_owned_client(db, client_id, user["username"])
    client.favorite = not bool(client.favorite)
    await db.commit()
    return {"success": True, "favorito": client.favorite}


@app.delete("/api/clientes/{client_id}")
@app.delete("/api/clientes/public/{client_id}")
async def delete_cliente(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Elimina cliente + CASCADE de operaciones y sus items.

    Hard delete: una baja lógica colisionaría con el UNIQUE
    (owner_username, email) si el user recrea un cliente con el mismo
    email. Las operaciones del cliente sí se borran físicamente.
    """
    username = user["username"]
    client = await _get_owned_client(db, client_id, username)

    # CASCADE: operation_items → operations del cliente (solo del user).
    op_rows = await db.execute(
        sa_select(OperationModel.id).where(
            OperationModel.client_id == client_id,
            OperationModel.owner_username == username,
        )
    )
    op_ids = [row[0] for row in op_rows.fetchall()]
    if op_ids:
        await db.execute(
            sa_delete(OperationItemModel).where(
                OperationItemModel.operation_id.in_(op_ids)
            )
        )
        await db.execute(
            sa_delete(OperationModel).where(
                OperationModel.id.in_(op_ids),
                OperationModel.owner_username == username,
            )
        )

    # Notas NCM asociadas al cliente (si las había vinculadas).
    await db.execute(
        sa_delete(NCMNoteModel).where(
            NCMNoteModel.client_id == client_id,
            NCMNoteModel.owner_username == username,
        )
    )

    await db.delete(client)
    await db.commit()
    return {
        "success": True,
        "message": "Cliente y operaciones eliminados",
        "operaciones_eliminadas": len(op_ids),
    }


@app.get("/api/clientes/{client_id}/operaciones")
async def get_client_operations(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Historial de operaciones del cliente (solo del user logueado)."""
    username = user["username"]
    # Verifica que el cliente sea del user (404 si no).
    await _get_owned_client(db, client_id, username)

    result = await db.execute(
        sa_select(OperationModel)
        .where(
            OperationModel.client_id == client_id,
            OperationModel.owner_username == username,
        )
        .order_by(sa_desc(OperationModel.created_at))
        .limit(50)
    )
    operations = result.scalars().all()
    return {
        "success": True,
        "operaciones": [
            {
                "id": op.id,
                "op_code": op.op_code,
                "fecha": op.created_at.isoformat() if op.created_at else None,
                "total_items": op.total_items,
                "total_value": op.total_value,
                "total_weight": op.total_weight,
                "generated_file": op.generated_file,
                "currency": op.currency,
            }
            for op in operations
        ],
    }


@app.post("/api/clientes/{client_id}/operaciones")
async def save_client_operation(
    client_id: str,
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Guarda una operación en el historial del cliente."""
    username = user["username"]
    await _get_owned_client(db, client_id, username)

    try:
        data = await request.json()
        op_code = data.get("operation_id") or f"OP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        resumen = data.get("resumen", {}) or {}
        items = data.get("items", []) or []

        operation = OperationModel(
            id=str(uuid.uuid4()),
            owner_username=username,
            client_id=client_id,
            op_code=op_code,
            source=data.get("source") or "manual",
            total_items=int(resumen.get("items", len(items))),
            total_value=float(resumen.get("valor_total", 0) or 0),
            currency=data.get("currency") or "USD",
            extra={"resumen": resumen},
        )
        db.add(operation)
        await db.flush()  # para tener operation.id

        for item in items:
            db.add(
                OperationItemModel(
                    id=str(uuid.uuid4()),
                    operation_id=operation.id,
                    pieza=str(item.get("pieza") or item.get("ncm") or "")[:10],
                    descripcion=str(item.get("descripcion") or ""),
                    origen=str(item.get("origen") or "XX")[:3],
                    cantidad=float(item.get("cantidad") or 1),
                    valor_unitario=float(item.get("valor_unitario") or 0),
                    peso_unitario=float(item.get("peso_unitario") or 0.5),
                )
            )

        # Alimentar la memoria de NCM del cliente: cada item con NCM +
        # descripcion se guarda (o actualiza) en ClientProductHistory. Esto
        # hace que la proxima op de este cliente sugiera NCMs automaticamente.
        try:
            from proyecto_maria.services.client_memory import upsert_client_product_history
        except ImportError:
            from services.client_memory import upsert_client_product_history

        for item in items:
            ncm_raw = str(item.get("ncm") or item.get("pieza") or "").strip()
            desc_raw = str(item.get("descripcion") or "").strip()
            if not ncm_raw or not desc_raw:
                continue
            try:
                await upsert_client_product_history(
                    db,
                    owner_username=username,
                    client_id=client_id,
                    ncm=ncm_raw,
                    descripcion=desc_raw,
                    origen=str(item.get("origen") or "").strip() or None,
                    valor_unitario=float(item.get("valor_unitario") or 0) or None,
                    cantidad=float(item.get("cantidad") or 0) or None,
                    peso_unitario=float(item.get("peso_unitario") or 0) or None,
                )
            except Exception:
                logging.exception(
                    "client_memory upsert fallo para client_id=%s ncm=%s",
                    client_id, ncm_raw,
                )
                # No rompemos el save de la operacion si la memoria falla.

        await db.commit()
        return {"success": True, "operation_id": operation.id, "op_code": op_code}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logging.exception("save_client_operation failed")
        return {"success": False, "error": "no se pudo guardar la operación"}


@app.get("/api/clientes/{client_id}/metricas")
async def get_client_metrics(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Métricas agregadas del historial del cliente."""
    username = user["username"]
    await _get_owned_client(db, client_id, username)

    result = await db.execute(
        sa_select(
            sa_func.count(OperationModel.id).label("total_operaciones"),
            sa_func.sum(OperationModel.total_items).label("total_items"),
            sa_func.sum(OperationModel.total_value).label("valor_total"),
            sa_func.max(OperationModel.created_at).label("ultimo"),
        ).where(
            OperationModel.client_id == client_id,
            OperationModel.owner_username == username,
        )
    )
    row = result.first()

    total_ops = int(row.total_operaciones or 0)
    total_items = int(row.total_items or 0)
    valor_total = float(row.valor_total or 0)
    ultimo = row.ultimo.strftime("%d/%m/%Y") if row.ultimo else "-"
    promedio = round(total_items / total_ops, 1) if total_ops > 0 else 0

    return {
        "total_operaciones": total_ops,
        "total_items": total_items,
        "valor_total": valor_total,
        "promedio_items_por_operacion": promedio,
        "ultimo_movimiento": ultimo,
    }


# === COLUMN MAPPING (Excel AVG) ===
# Canonicos soportados:
_CANON_COLUMNS = ["pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"]


def _sanitize_column_mapping(raw: dict) -> dict:
    """Normaliza un dict {header_origen: canonico} eliminando canonicos
    invalidos y claves vacias. Devuelve un dict limpio."""
    if not isinstance(raw, dict):
        return {}
    clean: dict[str, str] = {}
    for src, canon in raw.items():
        if not src:
            continue
        key = str(src).strip()
        val = str(canon or "").strip().lower()
        if not key:
            continue
        if val not in _CANON_COLUMNS:
            continue
        clean[key] = val
    return clean


@app.get("/api/clientes/{client_id}/column_mapping")
async def get_client_column_mapping(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el column mapping guardado del cliente (o {} si no hay)."""
    client = await _get_owned_client(db, client_id, user["username"])
    mapping = client.column_mapping if isinstance(client.column_mapping, dict) else {}
    return {
        "success": True,
        "cliente_id": client_id,
        "mapping": mapping or {},
        "canonicos": _CANON_COLUMNS,
    }


@app.post("/api/clientes/{client_id}/column_mapping")
async def set_client_column_mapping(
    client_id: str,
    body: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Guarda el column mapping del cliente. Body: {mapping: {header: canon}}."""
    client = await _get_owned_client(db, client_id, user["username"])
    raw = body.get("mapping") if isinstance(body, dict) else None
    clean = _sanitize_column_mapping(raw or {})
    client.column_mapping = clean or None
    await db.commit()
    await db.refresh(client)
    return {
        "success": True,
        "cliente_id": client_id,
        "mapping": client.column_mapping or {},
    }


@app.delete("/api/clientes/{client_id}/column_mapping")
async def delete_client_column_mapping(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Borra el column mapping del cliente."""
    client = await _get_owned_client(db, client_id, user["username"])
    client.column_mapping = None
    await db.commit()
    return {"success": True, "cliente_id": client_id, "mapping": {}}


@app.get("/api/clientes/{client_id}/plantilla")
async def download_client_template(
    client_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Genera y descarga una plantilla Excel (.xlsx) para que el cliente cargue
    su operación. Si el cliente tiene `column_mapping`, usa sus nombres
    originales como cabeceras; si no, usa los nombres canónicos."""
    client = await _get_owned_client(db, client_id, user["username"])

    mapping = client.column_mapping if isinstance(client.column_mapping, dict) else {}
    # Invertir mapping {source: canon} -> {canon: source}
    inv: dict[str, str] = {}
    for src, canon in (mapping or {}).items():
        if canon in _CANON_COLUMNS and src:
            inv[canon] = src
    headers = [inv.get(c, c) for c in _CANON_COLUMNS]

    import pandas as pd
    from datetime import datetime as _dt
    GENERATED_DIR = os.path.join(DATA_DIR, "generated")
    os.makedirs(GENERATED_DIR, exist_ok=True)

    df = pd.DataFrame(columns=headers)
    # Fila de ejemplo para guiar al cliente
    sample_row = {
        headers[0]: "84713000",
        headers[1]: "Laptop 14 pulgadas modelo X",
        headers[2]: "CN",
        headers[3]: 10,
        headers[4]: 350.0,
        headers[5]: 1.5,
    }
    df = pd.concat([df, pd.DataFrame([sample_row])], ignore_index=True)

    ts = _dt.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", (client.name or "cliente"))[:40]
    filename = f"PLANTILLA_{safe_name}_{ts}.xlsx"
    path = os.path.join(GENERATED_DIR, filename)
    df.to_excel(path, index=False, sheet_name="Items")

    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/plantillas/avg_blanco")
async def plantilla_avg_blanco(user=Depends(get_current_user)):
    """Descarga una plantilla Excel AVG en blanco (6 columnas canonicas + 1 fila
    de ejemplo) para que el despachante arranque a mano cuando no tiene PDF
    ni Excel del cliente.

    Idempotente: genera un archivo fresco con timestamp; no acumula estado.
    """
    import pandas as pd
    from datetime import datetime as _dt

    GENERATED_DIR = os.path.join(DATA_DIR, "generated")
    os.makedirs(GENERATED_DIR, exist_ok=True)

    headers = ["pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"]
    df = pd.DataFrame(columns=headers)
    sample = {
        "pieza": "84713000",
        "descripcion": "Laptop 14 pulgadas modelo X",
        "origen": "CN",
        "cantidad": 10,
        "valor_unitario": 350.0,
        "peso_unitario": 1.5,
    }
    df = pd.concat([df, pd.DataFrame([sample])], ignore_index=True)

    ts = _dt.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PLANTILLA_AVG_{ts}.xlsx"
    path = os.path.join(GENERATED_DIR, filename)
    df.to_excel(path, index=False, sheet_name="Items")

    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/upload_excel_v2/")
async def upload_excel_v2(
    request: Request,
    file: UploadFile = File(...),
    cliente_id: str | None = Form(default=None),
    use_mapping: bool = Form(default=True),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sube un Excel y lo convierte al formato items+operacion que espera la
    Review de v2. Si el usuario elige un cliente con `column_mapping`, las
    columnas se renombran a los canónicos antes de extraer.
    """
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo .xlsx o .xls")

    contents = await file.read()
    max_upload_bytes = _get_max_upload_bytes()
    if len(contents) > max_upload_bytes:
        max_mb = max_upload_bytes / 1024 / 1024
        raise HTTPException(
            status_code=413,
            detail=f"El archivo excede el tamaño máximo permitido ({max_mb:.0f} MB)",
        )

    mapping: dict = {}
    if cliente_id and use_mapping:
        try:
            c = await _get_owned_client(db, cliente_id, user["username"])
            if isinstance(c.column_mapping, dict):
                mapping = c.column_mapping
        except HTTPException:
            pass

    import tempfile
    safe_name = os.path.basename(file.filename).replace("..", "_")
    temp_fd, temp_filename = tempfile.mkstemp(suffix=os.path.splitext(safe_name)[1])
    try:
        with os.fdopen(temp_fd, "wb") as f:
            f.write(contents)

        engine = "openpyxl" if temp_filename.endswith(".xlsx") else "xlrd"
        df = pd.read_excel(temp_filename, engine=engine)

        # Aplicar mapping renombrando columnas a canonicas antes de extraer
        if mapping:
            rename = {src: canon for src, canon in mapping.items() if canon in _CANON_COLUMNS}
            df = df.rename(columns=rename)

        items = extract_items_from_excel(df, file.filename)
        if not items:
            raise HTTPException(
                status_code=400,
                detail="No se pudieron extraer items. Verificá el archivo o el mapeo de columnas.",
            )

        # Serializar items al shape que consume review/ncm en v2
        items_data = [
            {
                "pieza": str(getattr(it, "pieza", "") or ""),
                "descripcion": str(getattr(it, "descripcion", "") or ""),
                "origen": str(getattr(it, "origen", "XX") or "XX"),
                "cantidad": float(getattr(it, "cantidad", 1) or 1),
                "valor_unitario": float(getattr(it, "valor_unitario", 0) or 0),
                "peso_unitario": float(getattr(it, "peso_unitario", 0) or 0),
                "codigo_parte": str(getattr(it, "codigo_parte", "") or ""),
            }
            for it in items
        ]

        # Si hay cliente seleccionado, pre-populamos operacion con sus datos
        operacion: dict = {}
        if cliente_id:
            try:
                c = await _get_owned_client(db, cliente_id, user["username"])
                operacion = {
                    "comprador_nombre": c.name or "",
                    "comprador_cuit": c.cuit or "",
                    "comprador_domicilio": c.address or "",
                    "moneda": (c.preferred_currency or "USD"),
                }
            except HTTPException:
                operacion = {}

        return {
            "message": "Excel procesado exitosamente",
            "filename": file.filename,
            "items": items_data,
            "items_count": len(items_data),
            "operacion": operacion,
            "applied_mapping": bool(mapping),
        }
    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="El archivo Excel está vacío")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# === NOTAS POR NCM ===
# Las notas por NCM viven en tabla `ncm_notes` con owner_username.
# Ver endpoints `/api/ncm/notas/*` más abajo.

# ==================== VUCE: DATOS COMPLETOS NCM ====================

# Caché en memoria para evitar reconsultar el mismo NCM
_vuce_cache: dict = {}

@app.get("/api/ncm/{ncm}/completo")
async def get_ncm_completo_endpoint(ncm: str, user=Depends(get_current_user)):
    """
    Retorna datos completos de un NCM consultando VUCE + Tarifar (en modo mock).
    Incluye: descripción oficial, alícuotas, licencias requeridas, análisis de orígenes.
    Sin restricción de plan — disponible para todos los usuarios autenticados.
    """
    ncm_clean = re.sub(r'[^0-9]', '', ncm)[:8]
    if len(ncm_clean) < 6:
        raise HTTPException(status_code=400, detail="NCM debe tener al menos 6 dígitos")

    # Servir desde caché si está disponible (TTL: 1 hora)
    import time
    now = time.time()
    if ncm_clean in _vuce_cache:
        cached = _vuce_cache[ncm_clean]
        if now - cached['ts'] < 3600:
            return cached['data']

    try:
        from proyecto_maria.core.ncm_service import get_ncm_completo
        data = await get_ncm_completo(ncm_clean)
        _vuce_cache[ncm_clean] = {'data': data, 'ts': now}
        return data
    except Exception as e:
        logging.error(f"[VUCE] Error consultando NCM {ncm_clean}: {e}")
        # Fallback: usar solo vuce_connector directamente
        try:
            vuce_data = get_ncm_data(ncm_clean)
            return {
                "ncm": ncm_clean,
                "descripcion": vuce_data.get('descripcion', f'NCM {ncm_clean}'),
                "descripcion_vuce": vuce_data.get('descripcion'),
                "alicuotas": {
                    "arancel_extrazona": vuce_data.get('alicuotas', {}).get('arancel_base', 10.0),
                    "arancel_mercosur": 0.0,
                    "iva": vuce_data.get('alicuotas', {}).get('iva', 21.0),
                    "estadistica": vuce_data.get('alicuotas', {}).get('estadistica', 3.0),
                    "fuente": "vuce_mock"
                },
                "licencias": vuce_data.get('licencias', []),
                "regimen_especial": vuce_data.get('regimen_especial'),
                "unidad_medida": vuce_data.get('unidad_medida', 'KG'),
                "origen_preferencial": vuce_data.get('origen_preferencial', []),
                "analisis_origenes": None,
                "recomendacion_origen": None,
                "validacion": {"nivel_confianza": "medio", "fuentes_consultadas": {"vuce": True, "tarifar": False}},
                "metadata": {
                    "fecha_consulta": datetime.now().isoformat(),
                    "vuce_disponible": True,
                    "tarifar_disponible": False,
                    "modo_fake": True,
                    "version": "2.0-mock"
                }
            }
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Error consultando VUCE: {str(e2)}")


class NCMCacheRefreshRequest(BaseModel):
    ncm: str


@app.get("/api/system/connectors")
async def system_connectors(user=Depends(get_current_user)):
    """Estado de los conectores externos (VUCE, Tarifar, AFIP).

    Devuelve el modo efectivo y si las credenciales requeridas estan presentes.
    Util para QA, ops y un futuro panel de administracion. No expone las keys.
    """
    from proyecto_maria.core.vuce_connector import CONFIG as VUCE_CFG
    from proyecto_maria.core.tarifar_connector import TarifarConfig

    tarifar_cfg = TarifarConfig()
    afip_mode = (os.getenv("AFIP_MODE", "") or "").strip().lower() or (
        "api" if os.getenv("AFIP_CUIT") and os.getenv("AFIP_CERT_PATH") else "fake"
    )
    return {
        "vuce": {
            "mode": VUCE_CFG.mode,
            "has_api_key": bool(VUCE_CFG.api_key),
            "base_url": VUCE_CFG.base_url,
        },
        "tarifar": {
            "mode": tarifar_cfg.mode,
            "has_api_key": bool(tarifar_cfg.api_key),
            "base_url": tarifar_cfg.base_url,
            "note": "En mode=scrape usa los datos reales de NCM via scraper publico; el calculo en si es local.",
        },
        "afip": {
            "mode": afip_mode,
            "has_cuit": bool(os.getenv("AFIP_CUIT")),
            "has_cert": bool(os.getenv("AFIP_CERT_PATH")),
        },
        "ncm_scraper": {
            "user_agent": os.getenv(
                "NCM_SCRAPER_USER_AGENT",
                "CDI-NCM-Bot/1.0 (+https://cdi.local; contacto: soporte@cdi.local)",
            ),
            "min_interval_ms": int(os.getenv("NCM_SCRAPER_MIN_INTERVAL_MS", "1000")),
            "timeout_s": int(os.getenv("NCM_SCRAPER_TIMEOUT", "8")),
            "cache_ttl_hours": int(os.getenv("NCM_CACHE_TTL_HOURS", "168")),
        },
    }


@app.post("/api/ncm/cache/refresh")
async def refresh_ncm_cache(
    request_data: NCMCacheRefreshRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fuerza un re-fetch del NCM ignorando el cache DB + memoria.

    Util para despachante/admin cuando sospecha que el cache tiene un valor
    desactualizado (p. ej. hubo un decreto que cambio alicuotas). No requiere
    rol admin en la beta; cualquier usuario autenticado puede refrescar.
    """
    ncm_clean = re.sub(r"[^0-9]", "", request_data.ncm or "")[:8]
    if len(ncm_clean) < 6:
        raise HTTPException(status_code=400, detail="NCM debe tener al menos 6 digitos")

    # 1. Borrar cache DB
    try:
        from proyecto_maria.database.models import NCMCache as NCMCacheModel
        from sqlalchemy import delete as sa_delete
        await db.execute(sa_delete(NCMCacheModel).where(NCMCacheModel.ncm == ncm_clean))
        await db.commit()
    except Exception as err:
        logging.warning(f"[NCM cache refresh] no se pudo borrar cache DB: {err}")

    # 2. Invalidar cache en memoria
    _vuce_cache.pop(ncm_clean, None)

    # 3. Re-fetch
    try:
        from proyecto_maria.core.ncm_service import get_ncm_completo
        data = await get_ncm_completo(ncm_clean, refresh=True)
        import time
        _vuce_cache[ncm_clean] = {"data": data, "ts": time.time()}
        return {
            "success": True,
            "ncm": ncm_clean,
            "source": data.get("source", "unknown"),
            "data": data,
        }
    except Exception as err:
        logging.error(f"[NCM cache refresh] fallo re-fetch {ncm_clean}: {err}")
        raise HTTPException(status_code=502, detail=f"No se pudo refrescar NCM: {err}")


class EnrichItemsRequest(BaseModel):
    items: list


@app.post("/api/ncm/enrich-items")
async def enrich_items_vuce(request_data: EnrichItemsRequest, user=Depends(get_current_user)):
    """
    Enriquece una lista de items con datos VUCE (descripción oficial, alícuotas, licencias).
    Procesa todos los NCMs únicos en paralelo.
    Retorna los items originales + datos VUCE por NCM.
    """
    items = request_data.items
    if not items:
        return {"enriched": [], "licencias_warnings": [], "alicuotas_summary": {}}

    # Extraer NCMs únicos
    ncms_unicos = list({
        re.sub(r'[^0-9]', '', str(item.get('pieza', item.get('ncm', ''))))[:8]
        for item in items
        if item.get('pieza') or item.get('ncm')
    })
    ncms_unicos = [n for n in ncms_unicos if len(n) >= 6]

    # Consultar VUCE para cada NCM único
    vuce_por_ncm = {}
    import asyncio
    import time

    async def fetch_one(ncm: str):
        now = time.time()
        if ncm in _vuce_cache and now - _vuce_cache[ncm]['ts'] < 3600:
            return ncm, _vuce_cache[ncm]['data']
        try:
            from proyecto_maria.core.ncm_service import get_ncm_completo
            data = await get_ncm_completo(ncm)
            _vuce_cache[ncm] = {'data': data, 'ts': now}
            return ncm, data
        except Exception:
            # Fallback directo
            try:
                vuce_data = get_ncm_data(ncm)
                result = {
                    "ncm": ncm,
                    "descripcion": vuce_data.get('descripcion', f'NCM {ncm}'),
                    "alicuotas": {
                        "arancel_extrazona": vuce_data.get('alicuotas', {}).get('arancel_base', 10.0),
                        "arancel_mercosur": 0.0,
                        "iva": vuce_data.get('alicuotas', {}).get('iva', 21.0),
                        "estadistica": vuce_data.get('alicuotas', {}).get('estadistica', 3.0),
                        "fuente": "vuce_mock"
                    },
                    "licencias": vuce_data.get('licencias', []),
                    "regimen_especial": vuce_data.get('regimen_especial', 'General'),
                    "unidad_medida": vuce_data.get('unidad_medida', 'KG'),
                    "metadata": {"modo_fake": True, "vuce_disponible": True}
                }
                return ncm, result
            except Exception:
                return ncm, None

    results = await asyncio.gather(*[fetch_one(ncm) for ncm in ncms_unicos])
    for ncm, data in results:
        if data:
            vuce_por_ncm[ncm] = data

    # Construir items enriquecidos
    enriched = []
    licencias_warnings = []
    alicuotas_summary = {}

    for item in items:
        ncm_raw = str(item.get('pieza', item.get('ncm', '')))
        ncm_clean = re.sub(r'[^0-9]', '', ncm_raw)[:8]
        vuce = vuce_por_ncm.get(ncm_clean)

        enriched_item = dict(item)
        if vuce:
            enriched_item['vuce'] = {
                'descripcion_oficial': vuce.get('descripcion'),
                'alicuotas': vuce.get('alicuotas', {}),
                'licencias': vuce.get('licencias', []),
                'regimen_especial': vuce.get('regimen_especial'),
                'unidad_medida': vuce.get('unidad_medida', 'KG'),
                'modo_fake': vuce.get('metadata', {}).get('modo_fake', True)
            }
            # Acumular warnings de licencias
            for lic in vuce.get('licencias', []):
                if lic.get('requerida'):
                    licencias_warnings.append({
                        'ncm': ncm_clean,
                        'organismo': lic.get('codigo'),
                        'descripcion': lic.get('descripcion')
                    })
            # Resumen de alícuotas por NCM
            if ncm_clean not in alicuotas_summary and vuce.get('alicuotas'):
                alicuotas_summary[ncm_clean] = {
                    'descripcion': vuce.get('descripcion', f'NCM {ncm_clean}'),
                    'arancel': vuce['alicuotas'].get('arancel_extrazona', 10.0),
                    'iva': vuce['alicuotas'].get('iva', 21.0),
                    'estadistica': vuce['alicuotas'].get('estadistica', 3.0)
                }
        enriched.append(enriched_item)

    return {
        "enriched": enriched,
        "licencias_warnings": licencias_warnings,
        "alicuotas_summary": alicuotas_summary,
        "ncms_consultados": len(vuce_por_ncm),
        "modo_fake": True
    }


class CalculadoraRequest(BaseModel):
    """Input para la calculadora de tributos de v2.

    Valida que haya un NCM de al menos 6 dígitos y que valor_fob y cantidad
    sean positivos. `origen` se normaliza a mayúsculas/2 letras en el handler.
    Si `simular_origenes` es true, se corre ademas `get_simulacion_origen`
    para comparar costos CN/BR/PY/UY/etc.
    """
    ncm: str
    valor_fob: float
    cantidad: float = 1.0
    peso_unitario: float = 1.0
    origen: str = "CN"
    descripcion: str = ""
    simular_origenes: bool = True


@app.post("/api/ncm/calcular")
async def calcular_tributos(
    request_data: CalculadoraRequest,
    user=Depends(get_current_user),
):
    """Calcula tributos (DI, IVA, tasa estadistica, etc.) para un item hipotético.

    Delega en tarifar_connector. En modo fake devuelve estimaciones locales;
    en modo scrape/api usaria la fuente real. El despachante lo usa desde la
    pantalla NCM para estimar costo total antes de generar el MARIA.TXT.
    """
    from proyecto_maria.core.tarifar_connector import CLIENT as TARIFAR_CLIENT

    ncm_clean = re.sub(r"[^0-9]", "", request_data.ncm or "")[:8]
    if len(ncm_clean) < 6:
        raise HTTPException(status_code=400, detail="NCM debe tener al menos 6 digitos")
    if request_data.valor_fob <= 0:
        raise HTTPException(status_code=400, detail="valor_fob debe ser mayor a 0")
    if request_data.cantidad <= 0:
        raise HTTPException(status_code=400, detail="cantidad debe ser mayor a 0")

    origen = (request_data.origen or "CN").strip().upper()[:3] or "CN"

    item = {
        "pieza": ncm_clean,
        "descripcion": request_data.descripcion or f"Producto {ncm_clean}",
        "origen": origen,
        "cantidad": float(request_data.cantidad),
        "valor_unitario": float(request_data.valor_fob),
        "peso_unitario": float(request_data.peso_unitario),
    }

    try:
        calc = TARIFAR_CLIENT.calcular_aranceles([item])
    except Exception as err:
        logging.error(f"[calculadora] calcular_aranceles fallo: {err}")
        raise HTTPException(status_code=502, detail=f"No se pudo calcular: {err}")

    simulacion = None
    if request_data.simular_origenes:
        try:
            simulacion = TARIFAR_CLIENT.get_simulacion_origen(
                ncm=ncm_clean,
                valor_fob=float(request_data.valor_fob),
                cantidad=float(request_data.cantidad),
            )
        except Exception as err:
            # La comparacion es best-effort; no rompemos el calculo principal.
            logging.warning(f"[calculadora] simulacion_origen fallo: {err}")

    return {
        "success": True,
        "ncm": ncm_clean,
        "input": {
            "valor_fob": request_data.valor_fob,
            "cantidad": request_data.cantidad,
            "peso_unitario": request_data.peso_unitario,
            "origen": origen,
        },
        "calculo": calc,
        "simulacion_origenes": simulacion,
    }


# === NOTAS POR NCM (MULTI-TENANT) ===
# Notas privadas del despachante sobre un código NCM. Se almacenan en la
# tabla ncm_notes con owner_username. El indice idx es la POSICIÓN en la
# lista ordenada (más antiguas primero) filtrada por owner + ncm_code.


def _ncm_prefix(ncm: str) -> str:
    """Normaliza el NCM a sus primeros 4 dígitos (capítulo)."""
    clean = re.sub(r"[^0-9]", "", str(ncm or ""))
    return clean[:4]


async def _fetch_notas_ordered(db: AsyncSession, username: str, ncm_key: str):
    """Devuelve objetos NCMNote del user para ese NCM ordenados por fecha asc."""
    result = await db.execute(
        sa_select(NCMNoteModel)
        .where(
            NCMNoteModel.owner_username == username,
            NCMNoteModel.ncm_code == ncm_key,
        )
        .order_by(NCMNoteModel.created_at.asc())
    )
    return list(result.scalars().all())


@app.get("/api/ncm/notas/{ncm}")
async def get_ncm_notas(
    ncm: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene las notas del usuario para un NCM (capítulo de 4 dígitos)."""
    ncm_key = _ncm_prefix(ncm)
    if not ncm_key:
        return {"notas": []}
    notas = await _fetch_notas_ordered(db, user["username"], ncm_key)
    return {"notas": [n.note for n in notas]}


@app.post("/api/ncm/notas")
async def add_ncm_nota(
    data: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Agrega una nota al NCM (capítulo). Sin escape() en storage."""
    ncm_key = _ncm_prefix(data.get("ncm", ""))
    nota = str(data.get("nota", "")).strip()
    if not ncm_key or not nota:
        raise HTTPException(status_code=400, detail="NCM y nota son requeridos")

    db.add(
        NCMNoteModel(
            id=str(uuid.uuid4()),
            owner_username=user["username"],
            ncm_code=ncm_key,
            note=nota,
        )
    )
    await db.commit()
    return {"success": True, "message": f"Nota agregada a NCM {ncm_key}"}


@app.put("/api/ncm/notas/{ncm}/{idx}")
async def edit_ncm_nota(
    ncm: str,
    idx: int,
    data: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edita una nota existente (por índice posicional). Sin escape() en storage."""
    ncm_key = _ncm_prefix(ncm)
    nota_text = str(data.get("nota", "")).strip()

    notas = await _fetch_notas_ordered(db, user["username"], ncm_key)
    if idx < 0 or idx >= len(notas):
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    target = notas[idx]
    if nota_text:
        target.note = nota_text
    else:
        # Nota vacía → equivalente a eliminar.
        await db.delete(target)
    await db.commit()
    return {"success": True}


@app.delete("/api/ncm/notas/{ncm}/{idx}")
async def delete_ncm_nota(
    ncm: str,
    idx: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Elimina una nota (por índice posicional)."""
    ncm_key = _ncm_prefix(ncm)
    notas = await _fetch_notas_ordered(db, user["username"], ncm_key)
    if idx < 0 or idx >= len(notas):
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    await db.delete(notas[idx])
    await db.commit()
    return {"success": True}

# === SUGERIR NCM CON IA ===
NCM_HISTORIAL_FILE = os.path.join(DATA_DIR, 'ncm_historial.json')

def load_ncm_historial():
    """Carga historial de NCM usados por descripción"""
    if os.path.exists(NCM_HISTORIAL_FILE):
        try:
            with open(NCM_HISTORIAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Error loading NCM historial: {e}")
            return {}
    return {}

def save_ncm_historial(data):
    """Guarda historial de NCM"""
    with open(NCM_HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def normalizar_desc(desc: str) -> str:
    """Normaliza descripción para matching"""
    import re
    return re.sub(r'[^a-z0-9]', '', desc.lower())

@app.post("/api/ncm/sugerir")
async def sugerir_ncm(data: dict, user=Depends(get_current_user)):
    """Sugiere NCM basado en descripción: primero historial, luego IA.

    Requiere auth porque consume cuota de Gemini. El historial por ahora
    es shared (no por owner); se podria filtrar a futuro.
    """
    descripcion = data.get("descripcion", "").strip()
    if not descripcion or len(descripcion) < 3:
        return {"sugerencias": [], "error": "Descripción muy corta"}
    
    sugerencias = []
    desc_norm = normalizar_desc(descripcion)
    
    # 1. Buscar en historial
    historial = load_ncm_historial()
    for desc_guardada, ncm_data in historial.items():
        if desc_norm in normalizar_desc(desc_guardada) or normalizar_desc(desc_guardada) in desc_norm:
            sugerencias.append({
                "ncm": ncm_data.get("ncm", ""),
                "desc": desc_guardada[:50],
                "source": "historial",
                "count": ncm_data.get("count", 1)
            })
            if len(sugerencias) >= 2:
                break
    
    # 2. Si hay menos de 3, usar Gemini
    if len(sugerencias) < 3:
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview"))
            
            prompt = f"""Eres experto en comercio internacional MERCOSUR.
Para este producto: "{descripcion}"

Sugiere los 3 códigos NCM (Nomenclatura Común del Mercosur) más probables.
Responde SOLO en formato JSON array:
[{{"ncm": "8471.30", "desc": "Laptops y notebooks"}}, ...]

Solo el JSON, sin explicación."""

            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Parsear JSON
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                ia_sugerencias = json.loads(json_match.group())
                for sug in ia_sugerencias[:3 - len(sugerencias)]:
                    sugerencias.append({
                        "ncm": sug.get("ncm", ""),
                        "desc": sug.get("desc", ""),
                        "source": "ia"
                    })
        except Exception as e:
            print(f"⚠️ Error Gemini sugerencia NCM: {e}")
    
    return {"sugerencias": sugerencias[:3], "descripcion": descripcion}

@app.post("/api/ncm/guardar-uso")
async def guardar_uso_ncm(data: dict, user=Depends(get_current_user)):
    """Guarda el uso de un NCM para aprender del historial (requiere auth)."""
    descripcion = data.get("descripcion", "").strip()
    ncm = data.get("ncm", "").strip()
    
    if not descripcion or not ncm:
        return {"success": False}
    
    historial = load_ncm_historial()
    
    # Guardar o incrementar contador
    if descripcion in historial:
        historial[descripcion]["count"] = historial[descripcion].get("count", 0) + 1
        historial[descripcion]["ncm"] = ncm  # Actualizar NCM si cambió
    else:
        historial[descripcion] = {"ncm": ncm, "count": 1}
    
    save_ncm_historial(historial)
    return {"success": True}

# (file-based backup/restore removed — DB version at lines ~722-759 is used instead)

@app.get("/auth/me")
async def get_auth_me(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """Obtiene datos del usuario actual basado en el token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido: sin usuario")
        
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        
        if user:
            return {
                "username": username,
                "plan": user.plan,
                "roles": user.roles or []
            }
        else:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o corrupto")

# /logout is called by the frontend (app.js), must delete the auth cookie
@app.post("/logout")
def logout_root(response: Response):
    """Cierra sesión eliminando la cookie (alias de /auth/logout)"""
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada"}

@app.get("/features_integration.js")
def features_integration_js():
    """Sirve un JS vacío para evitar errores 404 y conflictos de variables"""
    return FileResponse(os.path.join(basedir, "proyecto_maria", "static", "dummy_features.js"), media_type="application/javascript")

# ============================================================================
# PAGOS - MercadoPago + Bitcoin
# ============================================================================
# WARNING (v1): estos endpoints /api/payments/* son del intento de integracion
# MP previo. Estado actual:
#  - webhook lee request.json() pero MP manda form-data / query params.
#  - pending_payments vive en memoria (se pierde al restart).
#  - la pagina /api/payments/success solo setea localStorage, no persiste
#    nada en DB. El User.plan no se actualiza de forma confiable.
#  - no valida la firma del webhook (x-signature).
# No estan cableados al flow de alta actual. El alta usa el billing simulado
# (ver CardInput + /api/billing/simulate-charge). Para produccion hay que:
#   a) arreglar este webhook (aceptar form, validar firma, persistir Payment)
#   b) o reemplazar todo por Stripe SetupIntent + webhook.
# ============================================================================
import uuid
import mercadopago
# HTMLResponse ya se importa arriba junto con FileResponse (bugfix: antes
# se usaba en el handler /dashboard antes de importarlo, lo que convertia
# cualquier error de template en NameError).

# Configuración MercadoPago (usar variable de entorno en producción)
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")

class PaymentRequest(BaseModel):
    plan: str = "premium"
    email: str = None
    username: str = None

class BitcoinPaymentRequest(BaseModel):
    amount_usd: float = 10.0
    email: str = None

# Almacenar pagos pendientes en memoria (en producción usar DB)
pending_payments = {}

@app.post("/api/payments/create-preference")
async def create_mercadopago_preference(request: PaymentRequest):
    """
    Crea una preferencia de pago en MercadoPago.
    Precio: $1 ARS para testing.
    """
    if not MP_ACCESS_TOKEN:
        # Modo demo sin credenciales reales
        demo_preference_id = f"demo_{uuid.uuid4().hex[:8]}"
        pending_payments[demo_preference_id] = {
            "status": "pending",
            "email": request.email,
            "username": request.username,
            "plan": request.plan,
            "amount": 1.0,
            "currency": "ARS"
        }
        return {
            "success": True,
            "mode": "demo",
            "preference_id": demo_preference_id,
            "init_point": f"/api/payments/demo-checkout/{demo_preference_id}",
            "message": "Modo demo - MP_ACCESS_TOKEN no configurado"
        }
    
    try:
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        
        preference_data = {
            "items": [
                {
                    "title": "CDI Premium - Plan Mensual",
                    "quantity": 1,
                    "unit_price": 100.0,  # $100 ARS
                    "currency_id": "ARS"
                }
            ],
            "external_reference": f"{request.username}|{request.plan}"
            # Nota: back_urls y auto_return requieren URLs públicas (no localhost)
            # Para producción, configurar con dominio real
        }
        
        if request.email:
            preference_data["payer"] = {"email": request.email}
        
        preference_response = sdk.preference().create(preference_data)
        print(f"📦 Respuesta MercadoPago: {preference_response}")
        
        # Verificar si hay error
        if preference_response.get("status") != 201:
            error_msg = preference_response.get("response", {})
            print(f"❌ Error MP: {error_msg}")
            raise HTTPException(status_code=400, detail=f"MercadoPago rechazó la solicitud: {error_msg}")
        
        preference = preference_response["response"]
        
        # Guardar referencia
        pending_payments[preference["id"]] = {
            "status": "pending",
            "email": request.email,
            "username": request.username,
            "plan": request.plan
        }
        
        # Detectar si estamos en modo sandbox (token empieza con TEST-)
        is_sandbox = MP_ACCESS_TOKEN.startswith("TEST-")
        
        return {
            "success": True,
            "mode": "sandbox" if is_sandbox else "live",
            "preference_id": preference["id"],
            "init_point": preference.get("sandbox_init_point") if is_sandbox else preference["init_point"],
            "sandbox_init_point": preference.get("sandbox_init_point")
        }
        
    except Exception as e:
        print(f"Error creando preferencia MP: {e}")
        raise HTTPException(status_code=500, detail=f"Error con MercadoPago: {str(e)}")

@app.get("/api/payments/demo-checkout/{preference_id}")
async def demo_checkout_page(preference_id: str):
    """Página de checkout demo cuando no hay credenciales MP"""
    if preference_id not in pending_payments:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    payment = pending_payments[preference_id]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Checkout - CDI</title>
        <style>
            body {{ font-family: system-ui; background: linear-gradient(135deg, #00b4e6 0%, #0066cc 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }}
            .checkout-box {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; text-align: center; }}
            h2 {{ color: #333; margin-bottom: 0.5rem; }}
            .price {{ font-size: 2.5rem; font-weight: bold; color: #00b4e6; margin: 1rem 0; }}
            .currency {{ font-size: 1rem; color: #666; }}
            .btn {{ background: #00b4e6; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; width: 100%; margin-top: 1rem; }}
            .btn:hover {{ background: #0099cc; }}
            .demo-notice {{ background: #fff3cd; color: #856404; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; }}
            .mp-logo {{ width: 150px; margin-bottom: 1rem; }}
        </style>
    </head>
    <body>
        <div class="checkout-box">
            <img src="https://www.mercadopago.com/org-img/MP3/home/logomp-color.svg" alt="MercadoPago" class="mp-logo">
            <div class="demo-notice">⚠️ Modo Demo - No se cobrará dinero real</div>
            <h2>CDI Premium</h2>
            <p>Plan Mensual</p>
            <div class="price">$1 <span class="currency">ARS</span></div>
            <button class="btn" onclick="confirmPayment()">✓ Simular Pago Exitoso</button>
        </div>
        <script>
            async function confirmPayment() {{
                const res = await fetch('/api/payments/demo-confirm/{preference_id}', {{ method: 'POST' }});
                const data = await res.json();
                if (data.success) {{
                    window.location.href = '/api/payments/success?demo=true&preference_id={preference_id}';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/api/payments/demo-confirm/{preference_id}")
async def demo_confirm_payment(preference_id: str):
    """Confirma un pago demo"""
    if preference_id not in pending_payments:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    pending_payments[preference_id]["status"] = "approved"
    return {"success": True, "message": "Pago demo confirmado"}

@app.get("/api/payments/success")
async def payment_success(preference_id: str = None, payment_id: str = None, demo: bool = False):
    """Página de éxito después del pago"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago Exitoso - CDI</title>
        <style>
            body { font-family: system-ui; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
            .success-box { background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); text-align: center; }
            .checkmark { font-size: 4rem; margin-bottom: 1rem; }
            h1 { color: #28a745; margin-bottom: 0.5rem; }
            p { color: #666; }
            .btn { background: #0066cc; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1rem; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 1.5rem; }
        </style>
    </head>
    <body>
        <div class="success-box">
            <div class="checkmark">✅</div>
            <h1>¡Pago Exitoso!</h1>
            <p>Tu cuenta Premium ha sido activada.</p>
            <p>Ya podés acceder a todas las funcionalidades.</p>
            <a href="/dashboard" class="btn">Ir al Dashboard</a>
        </div>
        <script>
            localStorage.setItem('user_plan', 'premium');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/api/payments/failure")
async def payment_failure():
    """Página de error en el pago"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago Fallido - CDI</title>
        <style>
            body { font-family: system-ui; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
            .error-box { background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); text-align: center; }
            .icon { font-size: 4rem; margin-bottom: 1rem; }
            h1 { color: #dc3545; margin-bottom: 0.5rem; }
            .btn { background: #0066cc; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1rem; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 1.5rem; }
        </style>
    </head>
    <body>
        <div class="error-box">
            <div class="icon">❌</div>
            <h1>Pago no procesado</h1>
            <p>Hubo un problema con tu pago. Por favor intentá de nuevo.</p>
            <a href="/" class="btn">Volver al inicio</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/api/payments/pending")
async def payment_pending():
    """Página de pago pendiente"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago Pendiente - CDI</title>
        <style>
            body { font-family: system-ui; background: linear-gradient(135deg, #ffc107 0%, #ffca2c 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
            .pending-box { background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); text-align: center; }
            .icon { font-size: 4rem; margin-bottom: 1rem; }
            h1 { color: #856404; margin-bottom: 0.5rem; }
            .btn { background: #0066cc; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1rem; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 1.5rem; }
        </style>
    </head>
    <body>
        <div class="pending-box">
            <div class="icon">⏳</div>
            <h1>Pago Pendiente</h1>
            <p>Tu pago está siendo procesado. Te notificaremos cuando se confirme.</p>
            <a href="/" class="btn">Volver al inicio</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/api/payments/webhook")
async def mercadopago_webhook(request: Request):
    """Webhook para recibir notificaciones de MercadoPago"""
    try:
        body = await request.json()
        print(f"📩 Webhook MP recibido: {body}")
        
        if body.get("type") == "payment":
            payment_id = body.get("data", {}).get("id")
            if payment_id and MP_ACCESS_TOKEN:
                sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info["response"]["status"] == "approved":
                    # Activar cuenta premium
                    external_ref = payment_info["response"].get("external_reference", "")
                    if "|" in external_ref:
                        username, plan = external_ref.split("|", 1)
                        print(f"✅ Pago aprobado para {username} - Plan: {plan}")
                        # Actualizar plan en DB
                        async for session in get_async_session():
                            result = await session.execute(select(User).where(User.username == username))
                            user = result.scalars().first()
                            if user:
                                user.plan = plan
                                await session.commit()
                                print(f"✅ Plan actualizado a {plan} para {username}")
                            break
        
        return {"success": True}
    except Exception as e:
        print(f"Error en webhook: {e}")
        return {"success": False, "error": str(e)}

# --- BITCOIN (Demo) ---
bitcoin_payments = {}

@app.post("/api/payments/bitcoin/create")
async def create_bitcoin_payment(request: BitcoinPaymentRequest):
    """
    Crea un pago Bitcoin demo.
    En producción usar BTCPay Server o Coinbase Commerce.
    """
    payment_id = f"btc_{uuid.uuid4().hex[:12]}"
    
    # Dirección demo (NO usar en producción)
    demo_address = f"bc1q{uuid.uuid4().hex[:38]}"
    
    # Precio simulado: $10 USD = ~0.00025 BTC
    btc_amount = round(request.amount_usd / 40000, 8)  # Precio BTC aprox
    
    bitcoin_payments[payment_id] = {
        "status": "pending",
        "address": demo_address,
        "amount_btc": btc_amount,
        "amount_usd": request.amount_usd,
        "email": request.email,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "payment_id": payment_id,
        "address": demo_address,
        "amount_btc": btc_amount,
        "amount_usd": request.amount_usd,
        "qr_data": f"bitcoin:{demo_address}?amount={btc_amount}",
        "expires_in": 900  # 15 minutos
    }

@app.get("/api/payments/bitcoin/checkout/{payment_id}")
async def bitcoin_checkout_page(payment_id: str):
    """Página de checkout Bitcoin"""
    if payment_id not in bitcoin_payments:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    payment = bitcoin_payments[payment_id]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago Bitcoin - CDI</title>
        <style>
            body {{ font-family: system-ui; background: linear-gradient(135deg, #f7931a 0%, #ffb347 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }}
            .checkout-box {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; text-align: center; }}
            h2 {{ color: #333; margin-bottom: 0.5rem; }}
            .btc-logo {{ font-size: 3rem; margin-bottom: 1rem; }}
            .amount {{ font-size: 1.5rem; font-weight: bold; color: #f7931a; margin: 1rem 0; }}
            .address {{ background: #f5f5f5; padding: 0.75rem; border-radius: 6px; font-family: monospace; font-size: 0.75rem; word-break: break-all; margin: 1rem 0; }}
            .qr-placeholder {{ width: 200px; height: 200px; background: #eee; margin: 1rem auto; display: flex; align-items: center; justify-content: center; border-radius: 8px; }}
            .btn {{ background: #f7931a; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; width: 100%; margin-top: 1rem; }}
            .btn:hover {{ background: #e8851a; }}
            .demo-notice {{ background: #fff3cd; color: #856404; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; }}
            .timer {{ color: #666; font-size: 0.9rem; margin-top: 0.5rem; }}
        </style>
    </head>
    <body>
        <div class="checkout-box">
            <div class="btc-logo">₿</div>
            <div class="demo-notice">⚠️ Modo Demo - Pago simulado</div>
            <h2>CDI Premium</h2>
            <div class="amount">{payment['amount_btc']} BTC</div>
            <p style="color: #666;">≈ ${payment['amount_usd']} USD</p>
            <div class="qr-placeholder">
                <span style="color: #999;">QR Code</span>
            </div>
            <div class="address">{payment['address']}</div>
            <p class="timer">⏱️ Expira en 15 minutos</p>
            <button class="btn" onclick="confirmPayment()">✓ Simular Pago Recibido</button>
        </div>
        <script>
            async function confirmPayment() {{
                const res = await fetch('/api/payments/bitcoin/confirm/{payment_id}', {{ method: 'POST' }});
                const data = await res.json();
                if (data.success) {{
                    window.location.href = '/api/payments/success?demo=true&method=bitcoin';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/api/payments/bitcoin/confirm/{payment_id}")
async def confirm_bitcoin_payment(payment_id: str):
    """Confirma un pago Bitcoin demo"""
    if payment_id not in bitcoin_payments:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    bitcoin_payments[payment_id]["status"] = "confirmed"
    return {"success": True, "message": "Pago Bitcoin confirmado"}


# ─────────────────────────────────────────────────────────────
# === CATÁLOGO DE PRODUCTOS POR PROVEEDOR ===
# ─────────────────────────────────────────────────────────────
try:
    from proyecto_maria.core import catalog_service as catalog_svc
    from proyecto_maria.core.catalog_service import is_valid_vendor_id
except ImportError:
    from core import catalog_service as catalog_svc
    from core.catalog_service import is_valid_vendor_id


def _require_valid_vendor_id(vendor_id: str) -> None:
    """Valida el formato del vendor_id para evitar path traversal / caracteres inválidos."""
    if not is_valid_vendor_id(vendor_id):
        raise HTTPException(status_code=400, detail="vendor_id inválido")


@app.post("/api/catalog/match")
async def catalog_match(
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Match items del PDF contra catálogo del proveedor."""
    try:
        body = await request.json()
        items = body.get("items", [])
        vendor_name = (body.get("vendor_name") or "").strip()
        if not vendor_name:
            return {"vendor_known": False, "vendor_id": "", "vendor_nombre": "",
                    "items_matched": [], "tasa_reconocimiento": 0,
                    "items_nuevos": len(items), "total_items": len(items)}
        return await catalog_svc.match_items(
            db, items, vendor_name, owner_username=user["username"]
        )
    except Exception as e:
        logging.exception("catalog_match error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/catalog/lookup")
async def catalog_lookup(
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lookup combinado: memoria del cliente + catalogo del proveedor.

    Prioridad por item:
      1. memoria del cliente (client_id + descripcion parecida) -> source="cliente"
      2. catalogo del proveedor (owner + vendor_name + descripcion) -> source="proveedor"
      3. sin match -> source="ninguno"

    Body esperado:
      {
        "items": [{"descripcion": "...", "pieza"?: "..."}],
        "vendor_name": "acme corp",
        "client_id": "uuid-del-cliente-opcional"
      }
    """
    try:
        body = await request.json()
        items = body.get("items", []) or []
        vendor_name = (body.get("vendor_name") or "").strip()
        client_id = (body.get("client_id") or "").strip() or None

        # Lookup en memoria del cliente (si hay client_id)
        try:
            from proyecto_maria.services.client_memory import lookup_client_memory
        except ImportError:
            from services.client_memory import lookup_client_memory

        # Lookup en catalogo del proveedor (batch)
        vendor_result = None
        if vendor_name:
            vendor_result = await catalog_svc.match_items(
                db, items, vendor_name, owner_username=user["username"]
            )
        vendor_matches_by_idx = {}
        if vendor_result and vendor_result.get("items_matched"):
            for m in vendor_result["items_matched"]:
                vendor_matches_by_idx[m["idx"]] = m

        enriched = []
        n_cliente = 0
        n_proveedor = 0

        for idx, item in enumerate(items):
            desc = (item.get("descripcion") or "").strip()
            out = {
                "idx": idx,
                "descripcion": desc,
                "source": "ninguno",
                "confidence": 0.0,
                "ncm": None,
                "origen": None,
            }

            # 1) memoria del cliente
            if client_id and desc:
                mem = await lookup_client_memory(db, user["username"], client_id, desc)
                if mem and mem.get("ncm"):
                    out.update({
                        "source": "cliente",
                        "confidence": mem["confidence"],
                        "ncm": mem["ncm"],
                        "origen": mem.get("origen") or None,
                        "veces_usado": mem.get("veces_usado"),
                        "peso_unitario_avg": mem.get("peso_unitario_avg"),
                        "valor_unitario_avg": mem.get("valor_unitario_avg"),
                        "ultima_vez": mem.get("ultima_vez"),
                    })
                    n_cliente += 1
                    enriched.append(out)
                    continue

            # 2) catalogo del proveedor
            vm = vendor_matches_by_idx.get(idx)
            if vm and vm.get("ncm") and vm.get("match_type") != "none":
                out.update({
                    "source": "proveedor",
                    "confidence": float(vm.get("match_score") or 0.0),
                    "ncm": vm.get("ncm"),
                    "origen": vm.get("origen"),
                    "unidad_medida": vm.get("unidad_medida"),
                    "match_type": vm.get("match_type"),
                })
                n_proveedor += 1

            enriched.append(out)

        total = len(items)
        return {
            "items": enriched,
            "total_items": total,
            "aplicados_cliente": n_cliente,
            "aplicados_proveedor": n_proveedor,
            "aplicados_total": n_cliente + n_proveedor,
            "sin_match": total - n_cliente - n_proveedor,
            "vendor_known": bool(vendor_result and vendor_result.get("vendor_known")),
            "vendor_id": (vendor_result or {}).get("vendor_id", ""),
            "vendor_nombre": (vendor_result or {}).get("vendor_nombre", vendor_name),
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("catalog_lookup error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/catalog/{vendor_id}/productos")
async def catalog_save_products(
    vendor_id: str,
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Guarda o actualiza productos en el catálogo de un proveedor."""
    _require_valid_vendor_id(vendor_id)
    try:
        body = await request.json()
        vendor_name = body.get("vendor_name", vendor_id)
        productos = body.get("productos", [])
        if not productos:
            raise HTTPException(status_code=400, detail="No se enviaron productos")
        return await catalog_svc.save_products(
            db, vendor_name, productos, owner_username=user["username"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("catalog_save error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog/proveedores")
async def catalog_list_vendors(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los proveedores conocidos en el catálogo."""
    try:
        vendors = await catalog_svc.list_vendors(db, owner_username=user["username"])
        return {"proveedores": vendors, "total": len(vendors)}
    except Exception as e:
        logging.exception("catalog_list error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog/{vendor_id}")
async def catalog_get_vendor(
    vendor_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el catálogo completo de un proveedor."""
    _require_valid_vendor_id(vendor_id)
    vendor = await catalog_svc.get_vendor_by_id(db, vendor_id, owner_username=user["username"])
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Proveedor '{vendor_id}' no encontrado")
    return {
        "vendor_id": vendor_id,
        "nombre": vendor.get("nombre", vendor_id),
        "productos": vendor.get("productos", {}),
        "total_productos": len(vendor.get("productos", {})),
        "ultima_actualizacion": vendor.get("ultima_actualizacion"),
    }


def _validate_product_key(product_key: str) -> None:
    """Sanity-check defensivo de la clave de producto que llega por path."""
    if not product_key or len(product_key) > 500:
        raise HTTPException(status_code=400, detail="product_key inválido")


@app.put("/api/catalog/{vendor_id}/productos/{product_key:path}")
async def catalog_update_product(
    vendor_id: str,
    product_key: str,
    request: Request,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un producto individual del catálogo de un proveedor."""
    _require_valid_vendor_id(vendor_id)
    _validate_product_key(product_key)
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Body debe ser un objeto JSON")
        if not await catalog_svc.get_vendor_by_id(db, vendor_id, owner_username=user["username"]):
            raise HTTPException(status_code=404, detail=f"Proveedor '{vendor_id}' no encontrado")
        updated = await catalog_svc.update_product(
            db, vendor_id, product_key, body, owner_username=user["username"]
        )
        if updated is None:
            raise HTTPException(
                status_code=404,
                detail=f"Producto '{product_key}' no existe o la nueva descripción colisiona con otro producto",
            )
        return {"success": True, "vendor_id": vendor_id, "producto": updated}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("catalog_update_product error")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/catalog/{vendor_id}/productos/{product_key:path}")
async def catalog_delete_product(
    vendor_id: str,
    product_key: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Borra un producto individual del catálogo de un proveedor (idempotente)."""
    _require_valid_vendor_id(vendor_id)
    _validate_product_key(product_key)
    try:
        deleted = await catalog_svc.delete_product(
            db, vendor_id, product_key, owner_username=user["username"]
        )
        return {"success": True, "deleted": deleted, "vendor_id": vendor_id}
    except Exception as e:
        logging.exception("catalog_delete_product error")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/catalog/{vendor_id}")
async def catalog_delete_vendor(
    vendor_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Borra un proveedor completo del catálogo (idempotente)."""
    _require_valid_vendor_id(vendor_id)
    try:
        deleted = await catalog_svc.delete_vendor(
            db, vendor_id, owner_username=user["username"]
        )
        return {"success": True, "deleted": deleted, "vendor_id": vendor_id}
    except Exception as e:
        logging.exception("catalog_delete_vendor error")
        raise HTTPException(status_code=500, detail=str(e))
