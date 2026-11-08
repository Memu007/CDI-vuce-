import os
from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# En producción DEBE sobreescribirse con JWT_SECRET_KEY (o SECRET_KEY).
_DEFAULT_DEV_SECRET = "tu-clave-secreta-super-segura-cambiar-en-produccion"


def es_desarrollo() -> bool:
    # Sin la variable o con un valor desconocido, la app se porta como en producción.
    return os.getenv("ENVIRONMENT") in ("development", "test", "testing")


def get_frontend_url() -> str:
    """Base pública de la UI para los links de los emails y la vuelta del cobro."""
    url = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    if url:
        return url
    if not es_desarrollo():
        raise RuntimeError(
            "FRONTEND_URL no esta seteada y ENVIRONMENT no es development, test ni testing. "
            "Definir p.ej. FRONTEND_URL=https://cdi.tu-dominio.com"
        )
    return "http://127.0.0.1:8010"


class Settings(BaseSettings):
    # JWT Configuration
    # Lee JWT_SECRET_KEY → SECRET_KEY → JWT_SECRET. Firma y verificación la
    # toman sólo de acá (auth/dependencies.py).
    jwt_secret: str = Field(
        default=_DEFAULT_DEV_SECRET,
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY", "JWT_SECRET"),
    )
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    # Rate Limiting (diferenciado por plan)
    # Ajustado para soportar 2000 usuarios (200 concurrentes)
    rate_limit: str = Field("3000/minute", alias="API_RATE_LIMIT")  # Legacy - aumentado desde 100/min
    rate_limit_basic: str = Field("3000/minute", alias="RATE_LIMIT_BASIC")  # aumentado desde 100/min
    rate_limit_premium: str = Field("5000/minute", alias="RATE_LIMIT_PREMIUM")  # aumentado desde 500/min

    # File Upload Limits
    max_file_size_basic_mb: int = Field(10, alias="MAX_FILE_SIZE_BASIC_MB")
    max_file_size_premium_mb: int = Field(50, alias="MAX_FILE_SIZE_PREMIUM_MB")

    # External APIs
    firebase_credentials: Optional[str] = Field(default=None, alias="FIREBASE_CREDENTIALS")
    vuce_base_url: str = Field("https://sandbox.vuce.gob.ar/api", alias="VUCE_BASE_URL")
    vuce_api_key: Optional[str] = Field(default=None, alias="VUCE_API_KEY")
    vuce_fake_mode: bool = Field(True, alias="VUCE_FAKE_MODE")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    enable_pdf_llm_fallback: bool = Field(True, alias="ENABLE_PDF_LLM_FALLBACK")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
