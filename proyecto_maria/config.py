from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # JWT Configuration
    jwt_secret: str = Field("change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_exp_minutes: int = Field(60, alias="JWT_EXP_MINUTES")

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
