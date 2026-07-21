"""
backend/app/config.py
=====================
Configuración de la aplicación FastAPI usando pydantic-settings.

Las variables se leen en este orden de prioridad:
  1. Variables de entorno del sistema
  2. Archivo .env en la raíz del proyecto
  3. Valores por defecto definidos aquí

Uso
---
from backend.app.config import settings
print(settings.DATABASE_URL)
"""

import secrets
import warnings
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Base de datos ──────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://kwesx:kwesx_dev_2026@localhost:5433/kwesx_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://kwesx:kwesx_dev_2026@localhost:5433/kwesx_db"

    # ── API ────────────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"   # "production" en Render/Docker
    SECRET_KEY: str = "cambia-esto-en-produccion"

    # ── Rate Limiting ──────────────────────────────────────────────────────
    RATE_LIMIT_CHAT: str = "30/minute"
    RATE_LIMIT_DATOS: str = "120/minute"
    RATE_LIMIT_ML: str = "20/minute"

    # ── Proyecto ───────────────────────────────────────────────────────────
    PROJECT_NAME: str = "Kwesx AI"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = (
        "Sistema Operativo Territorial Inteligente para Colombia. "
        "Transforma datos abiertos en inteligencia territorial mediante IA. "
        "Integra ANI, UPRA, IDEAM, DANE, MinTIC y más fuentes oficiales."
    )
    PROJECT_TAGS: list[str] = ["govtech", "colombia", "datos-abiertos", "ia-territorial"]

    # ── ETL ────────────────────────────────────────────────────────────────
    SOCRATA_APP_TOKEN: str = ""
    ETL_TIMEOUT_SECONDS: int = 30
    ETL_MAX_RETRIES: int = 3

    # ── Cache ──────────────────────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = 300   # 5 minutos por defecto

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def debug(self) -> bool:
        return not self.is_production

    def validate_security(self) -> None:
        """Alerta si la configuración no es segura para producción."""
        if self.is_production and self.SECRET_KEY == "cambia-esto-en-produccion":
            warnings.warn(
                "⚠️  SECRET_KEY usa el valor por defecto en producción. "
                "Establece SECRET_KEY en las variables de entorno.",
                stacklevel=2,
            )


# Instancia global — importar desde aquí en todos los módulos
settings = Settings()

# Verificar seguridad al cargar
settings.validate_security()
