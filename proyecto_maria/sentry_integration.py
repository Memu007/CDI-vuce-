"""
Sentry Error Tracking Integration
Professional error monitoring and performance tracking for production
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging


def init_sentry(
    dsn: str,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
    enable_tracing: bool = True
):
    """
    Inicializa Sentry con integración completa de FastAPI.

    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Entorno de deployment (development, staging, production)
        traces_sample_rate: % de transacciones a trackear (0.0 - 1.0)
        enable_tracing: Habilitar performance tracing
    """
    # Logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capturar INFO y superior
        event_level=logging.ERROR  # Enviar ERROR+ como eventos
    )

    # FastAPI integration
    fastapi_integration = FastApiIntegration(
        transaction_style="url"  # Agrupar por URL pattern
    )

    # SQLAlchemy integration (si se usa DB)
    sqlalchemy_integration = SqlalchemyIntegration()

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        enable_tracing=enable_tracing,
        integrations=[
            fastapi_integration,
            logging_integration,
            sqlalchemy_integration
        ],
        # Filtrar información sensible
        before_send=before_send_filter,
        # Configuración de release (opcional)
        # release="maria@1.0.0",
        # Configuración de sampling
        sample_rate=1.0,  # 100% de errores
        # Debug mode (solo para desarrollo)
        debug=False,
        # Attach stack locals (útil para debugging)
        attach_stacktrace=True,
        # Request bodies
        request_bodies="medium",  # "always", "medium", "never"
        # Max breadcrumbs
        max_breadcrumbs=100,
        # Tag defaults
        default_integrations=True
    )

    # Tag con información adicional
    sentry_sdk.set_tag("service", "maria-backend")
    sentry_sdk.set_tag("language", "python")


def before_send_filter(event, hint):
    """
    Filtro para sanitizar datos sensibles antes de enviar a Sentry.

    Args:
        event: Evento de Sentry
        hint: Información adicional del evento

    Returns:
        Event modificado o None para descartarlo
    """
    # Remover información sensible de request data
    if 'request' in event:
        request = event['request']

        # Sanitizar headers
        if 'headers' in request:
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '[REDACTED]'

        # Sanitizar query params
        if 'query_string' in request:
            sensitive_params = ['api_key', 'token', 'password']
            for param in sensitive_params:
                if param in str(request.get('query_string', '')):
                    request['query_string'] = '[REDACTED]'

        # Sanitizar body
        if 'data' in request:
            data = request['data']
            if isinstance(data, dict):
                sensitive_keys = ['password', 'api_key', 'secret', 'token', 'cuit']
                for key in sensitive_keys:
                    if key in data:
                        data[key] = '[REDACTED]'

    # Remover variables locales sensibles
    if 'exception' in event:
        if 'values' in event['exception']:
            for exception in event['exception']['values']:
                if 'stacktrace' in exception:
                    if 'frames' in exception['stacktrace']:
                        for frame in exception['stacktrace']['frames']:
                            if 'vars' in frame:
                                sensitive_vars = ['password', 'api_key', 'secret', 'token']
                                for var in sensitive_vars:
                                    if var in frame['vars']:
                                        frame['vars'][var] = '[REDACTED]'

    return event


def set_user_context(user_id: str, email: str = None, plan: str = None):
    """
    Asocia información de usuario al contexto de Sentry.

    Args:
        user_id: ID del usuario
        email: Email del usuario (opcional)
        plan: Plan del usuario (basic, premium, etc.)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "plan": plan
    })


def add_breadcrumb(message: str, category: str = "custom", level: str = "info", data: dict = None):
    """
    Agrega un breadcrumb (trazabilidad de eventos) a Sentry.

    Args:
        message: Mensaje descriptivo del evento
        category: Categoría del evento (api, database, cache, etc.)
        level: Nivel de severidad (debug, info, warning, error)
        data: Datos adicionales del evento
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def capture_exception(exception: Exception, context: dict = None):
    """
    Captura una excepción manualmente y la envía a Sentry.

    Args:
        exception: Excepción a capturar
        context: Contexto adicional (dict con tags, extra data, etc.)
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            # Agregar tags
            if 'tags' in context:
                for key, value in context['tags'].items():
                    scope.set_tag(key, value)

            # Agregar extra data
            if 'extra' in context:
                for key, value in context['extra'].items():
                    scope.set_extra(key, value)

            # Agregar contexto de usuario
            if 'user' in context:
                scope.set_user(context['user'])

            sentry_sdk.capture_exception(exception)
    else:
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    Captura un mensaje personalizado y lo envía a Sentry.

    Args:
        message: Mensaje a enviar
        level: Nivel de severidad (debug, info, warning, error, fatal)
        context: Contexto adicional
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            if 'tags' in context:
                for key, value in context['tags'].items():
                    scope.set_tag(key, value)

            if 'extra' in context:
                for key, value in context['extra'].items():
                    scope.set_extra(key, value)

            sentry_sdk.capture_message(message, level=level)
    else:
        sentry_sdk.capture_message(message, level=level)


# Ejemplo de uso:
"""
# En startup del servidor (server_funcional.py):
from sentry_integration import init_sentry

init_sentry(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=0.1
)

# En endpoints:
from sentry_integration import set_user_context, add_breadcrumb, capture_exception

@app.post("/api/process")
async def process_data(request: Request):
    try:
        # Asociar usuario
        set_user_context(user_id="123", email="user@example.com", plan="premium")

        # Agregar breadcrumbs para trazabilidad
        add_breadcrumb("Processing started", category="api", data={"endpoint": "/api/process"})

        # Tu código aquí
        result = do_something()

        add_breadcrumb("Processing completed", category="api", level="info")

        return {"success": True, "result": result}

    except Exception as e:
        # Capturar error con contexto
        capture_exception(e, context={
            "tags": {"endpoint": "/api/process", "user_plan": "premium"},
            "extra": {"request_data": request_data}
        })
        raise
"""
