"""
Database models for MARIA project using SQLAlchemy.

Multi-tenant: cada modelo con datos del despachante tiene `owner_username`
(FK a users.username) para aislar datos por usuario. Ver
`docs/AUDIT_MULTITENANT.md` para el plan completo.
"""

from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Float, Boolean, JSON,
    ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from proyecto_maria.database.connection import Base


class User(Base):
    """Usuario del sistema (despachante)."""
    __tablename__ = "users"

    username = Column(String(50), primary_key=True)
    email = Column(String(100), unique=True, nullable=True)
    password = Column(String(255), nullable=False)  # Hashed
    name = Column(String(100), nullable=True)
    # CUIT del despachante (emite el TXT AVG como CDDTAGR en cabecera DDT).
    # Es por usuario y no cambia entre operaciones, por eso vive en el perfil
    # y no en cada MariaRequest (aunque sigue aceptandose via request).
    cuit = Column(String(15), nullable=True)
    # Defaults de operacion del despachante: si tiene cargados estos en perfil,
    # se usan como fallback en cada operacion en vez de los defaults globales
    # (ARBUE/001/IC04). El usuario puede pisarlos por operacion en Revisar.
    default_aduana_codigo = Column(String(10), nullable=True)
    default_puerto_destino = Column(String(10), nullable=True)
    default_tipo_destinacion = Column(String(10), nullable=True)
    plan = Column(String(20), default="trial")
    roles = Column(JSON, default=[])
    is_verified = Column(Boolean, default=False)

    # Multi-puesto / equipo (T5-lite, Sprint 25 Día 2):
    # Si NULL, el user es su propio "team" (comportamiento por defecto).
    # Si tiene valor, sus queries de tenant deben filtrar por team_owner_username
    # en lugar de username (refactor pendiente para T5-full, on-demand).
    # FK self-referencial a users.username.
    team_owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,
        index=True,
    )

    # Organización (estudio). Si tiene valor, el user es miembro de un estudio
    # y su billing se lee de la Organization, no de su propio User.
    organization_id = Column(
        String,
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )

    # --- Billing (simulated / stripe / mercadopago) ---
    # none=sin pm cargado, trial=prueba gratis, active=cobrando, past_due=trial
    # vencido sin cobro exitoso, canceled=dado de baja.
    billing_status = Column(String(20), default="none")
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    payment_provider = Column(String(20), nullable=True)
    payment_customer_id = Column(String(100), nullable=True)
    payment_method_last4 = Column(String(4), nullable=True)
    payment_method_brand = Column(String(20), nullable=True)

    # Ola 4: contadores y metadata de suscripción/tarjeta.
    mp_preapproval_id = Column(String(100), nullable=True)
    mp_plan_id = Column(String(100), nullable=True)
    ops_used_this_period = Column(Integer, default=0)
    extra_ops_remaining = Column(Integer, default=0)
    billing_period_started_at = Column(DateTime(timezone=True), nullable=True)
    last_topup_at = Column(DateTime(timezone=True), nullable=True)

    # Ola 4 robustez: evitar reprocesar el mismo pago MP; créditos extra expiran.
    last_payment_id = Column(String(100), nullable=True)
    extra_ops_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    clients = relationship("Client", back_populates="owner")
    operations = relationship("Operation", back_populates="owner")


class PasswordResetToken(Base):
    """Token para recuperación de contraseña."""
    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_username = Column(String(50), ForeignKey("users.username"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="password_reset_tokens")


class Client(Base):
    """Cliente/Importador en el sistema.

    Multi-tenant: `owner_username` determina a qué despachante pertenece.
    Email NO es unique globalmente; puede repetirse entre despachantes.
    """
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("owner_username", "email", name="uq_clients_owner_email"),
        Index("ix_clients_owner", "owner_username"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,  # nullable durante la migración; se vuelve NOT NULL tras backfill
        index=True,
    )

    name = Column(String(200), nullable=False)
    email = Column(String(100), nullable=True)  # unique removido (ver UniqueConstraint)
    phone = Column(String(50), nullable=True)
    cuit = Column(String(15), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    favorite = Column(Boolean, default=False)

    default_origin = Column(String(3), default="CN")
    preferred_currency = Column(String(3), default="USD")
    auto_ncm_enabled = Column(Boolean, default=True)
    # Fecha de inicio de actividad del importador (formato ISO YYYY-MM-DD).
    # Se propaga a comprador_fecha_inic_activ en operaciones que usan este cliente.
    fecha_inic_activ = Column(String(10), nullable=True)
    # Mapeo de columnas de Excel -> canonicos {header_origen: canonico}
    # Canonicos: pieza | descripcion | origen | cantidad | valor_unitario | peso_unitario
    column_mapping = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    owner = relationship("User", back_populates="clients")
    operations = relationship("Operation", back_populates="client")
    ncm_notes = relationship("NCMNote", back_populates="client")


class Operation(Base):
    """Operación de importación procesada."""
    __tablename__ = "operations"
    __table_args__ = (
        Index("ix_operations_owner", "owner_username"),
        Index("ix_operations_owner_created", "owner_username", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,
        index=True,
    )
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    op_code = Column(String(100), nullable=True)  # identificador amigable (AVG_GROUPED_...)
    operation_type = Column(String(20), default="import")
    source = Column(String(50), nullable=True)  # p.ej. "grouped", "pdf_upload"
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Float, nullable=True)

    source_file = Column(String(255), nullable=True)
    generated_file = Column(String(255), nullable=True)
    extraction_method = Column(String(50), nullable=True)

    total_items = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)
    total_weight = Column(Float, default=0.0)
    processing_time_ms = Column(Integer, nullable=True)

    # Cockpit: estado del despacho (borrador -> oficializada -> canal -> liberada)
    estado = Column(String(20), default="borrador")
    # Canal aduanero asignado: verde / naranja / rojo (None hasta oficializar)
    canal = Column(String(10), nullable=True)

    # Blob flexible para datos auxiliares (resumen, items snapshot, etc.)
    extra = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="operations")
    client = relationship("Client", back_populates="operations")
    items = relationship("OperationItem", back_populates="operation")


class OperationItem(Base):
    """Item individual dentro de una operación."""
    __tablename__ = "operation_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id = Column(String, ForeignKey("operations.id"), nullable=False)

    pieza = Column(String(10), nullable=False)  # NCM code
    descripcion = Column(Text, nullable=False)
    origen = Column(String(3), nullable=False)
    cantidad = Column(Float, nullable=False)
    valor_unitario = Column(Float, nullable=False)
    peso_unitario = Column(Float, nullable=False)

    marca = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)

    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)

    operation = relationship("Operation", back_populates="items")


class NCMNote(Base):
    """Notas y observaciones sobre códigos NCM específicos.

    Multi-tenant: `owner_username` puede ser None para notas "sistema"
    visibles a todos, o un username concreto para notas privadas del
    despachante.
    """
    __tablename__ = "ncm_notes"
    __table_args__ = (
        Index("ix_ncm_notes_owner_ncm", "owner_username", "ncm_code"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,
        index=True,
    )
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)

    ncm_code = Column(String(10), nullable=False)
    note = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="ncm_notes")


class SystemBackup(Base):
    """Backups del sistema y datos de localStorage.

    `owner_username` puede ser None para backups de sistema.
    """
    __tablename__ = "system_backups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,
        index=True,
    )

    backup_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=True)
    data_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    size_bytes = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)


class APILog(Base):
    """Log de llamadas a APIs externas y uso del sistema."""
    __tablename__ = "api_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,
        index=True,
    )

    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    operation_id = Column(String, ForeignKey("operations.id"), nullable=True)
    external_api = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClientProductHistory(Base):
    """Historial de productos procesados por cliente para auto-completado inteligente."""
    __tablename__ = "client_product_history"
    __table_args__ = (
        Index("ix_cph_owner_client", "owner_username", "client_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=True,
        index=True,
    )
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)

    ncm = Column(String(10), nullable=False)
    descripcion = Column(Text, nullable=False)
    descripcion_normalizada = Column(String(200), nullable=True)

    peso_unitario_avg = Column(Float, default=0.0)
    origen_frecuente = Column(String(3), default="XX")
    veces_usado = Column(Integer, default=1)

    valor_unitario_avg = Column(Float, nullable=True)
    cantidad_avg = Column(Float, nullable=True)

    primera_vez = Column(DateTime(timezone=True), server_default=func.now())
    ultima_vez = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client", backref="product_history")


class VendorCatalogProduct(Base):
    """Catalogo de productos por proveedor (persistido en DB, antes JSON).

    Reemplaza `product_catalog.json` que se perdia con cada deploy. Tenant
    aislado por `owner_username`. Para el mismo vendor, cada combinacion
    (owner, vendor_id, product_key) es unica. `product_key` es la
    descripcion normalizada (ver `catalog_service._normalize`).
    """
    __tablename__ = "vendor_catalog_products"
    __table_args__ = (
        UniqueConstraint(
            "owner_username", "vendor_id", "product_key",
            name="uq_vendor_catalog",
        ),
        Index("ix_vcp_owner_vendor", "owner_username", "vendor_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        index=True,
        nullable=False,
    )
    vendor_id = Column(String(100), nullable=False)
    vendor_nombre = Column(String(200), nullable=True)

    product_key = Column(String(300), nullable=False)
    descripcion = Column(String(500), nullable=True)
    ncm = Column(String(20), nullable=True)
    origen = Column(String(5), nullable=True)
    valor_unitario = Column(Float, nullable=True)
    peso_unitario = Column(Float, nullable=True)

    usos = Column(Integer, default=1)
    primera_vez = Column(DateTime(timezone=True), server_default=func.now())
    ultima_vez = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    extra = Column(JSON, nullable=True)


class TelemetryEvent(Base):
    """Eventos de uso de la UI (telemetría opcional).

    Persisten en SQL para KPIs y diagnóstico; siguen coexistiendo con el log
    JSONL en disco.
    """

    __tablename__ = "telemetry_events"
    __table_args__ = (Index("ix_telemetry_created", "created_at"),)

    id = Column(String(36), primary_key=True)
    owner_username = Column(String(50), nullable=True, index=True)
    action = Column(String(120), nullable=False)
    screen = Column(String(80), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    props = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NCMCache(Base):
    """Cache persistente de datos enriquecidos de NCM (VUCE/Tarifar/scrape).

    Guardamos el payload unificado (alicuotas, licencias, regimen, descripcion)
    por NCM para evitar golpear fuentes externas en cada request. El TTL se
    define a nivel aplicacion (env `NCM_CACHE_TTL_HOURS`) y se compara contra
    `expires_at`. Es global (sin `owner_username`) porque los datos de NCM
    son publicos y no dependen del despachante.
    """
    __tablename__ = "ncm_cache"
    __table_args__ = (
        Index("ix_ncm_cache_expires", "expires_at"),
    )

    ncm = Column(String(10), primary_key=True)
    payload = Column(JSON, nullable=False)
    source = Column(String(32), nullable=False)  # scrape:tarifar | scrape:arancel | api:vuce | fake | manual
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)


class PublicQuote(Base):
    """Snapshot de presupuesto arancelario para compartir con clientes.
    
    Generado a partir de una Operation existente, inmutable y con expiración.
    Accesible públicamente mediante el token_id.
    """
    __tablename__ = "public_quotes"
    
    # token_id generado con secrets.token_urlsafe(16)
    token_id = Column(String(50), primary_key=True)
    operation_id = Column(String, ForeignKey("operations.id"), nullable=False)
    
    # Snapshot JSON con los datos arancelarios calculados y el branding de la empresa
    snapshot_data = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    operation = relationship("Operation")


class Organization(Base):
    """Estudio de despachantes: un admin paga, varios usuarios operan."""
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    owner_username = Column(
        String(50),
        ForeignKey("users.username"),
        nullable=False,
        index=True,
    )

    # Billing de la org (espeja los campos de User)
    plan = Column(String(20), default="premium")
    billing_status = Column(String(20), default="none")
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    ops_used_this_period = Column(Integer, default=0)
    extra_ops_remaining = Column(Integer, default=0)
    mp_preapproval_id = Column(String(100), nullable=True)
    mp_plan_id = Column(String(100), nullable=True)
    billing_period_started_at = Column(DateTime(timezone=True), nullable=True)
    last_payment_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("User", foreign_keys="User.organization_id", backref="organization")
    invitations = relationship("Invitation", back_populates="org")


class Invitation(Base):
    """Invitación a unirse a una organización."""
    __tablename__ = "invitations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(100), nullable=False)
    token = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default="pending")  # pending / accepted / expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    org = relationship("Organization", back_populates="invitations")
