from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator

class Settings(BaseSettings):
    """Central application configuration, populated from environment variables / .env.

    Nothing here should ever be hardcoded per-environment: local dev, staging, and
    production all read the same class with different .env files.
    """

    DATABASE_URL: str = "postgresql+psycopg2://shift_user:shift_password@localhost:5432/shift_db"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INVITE_EXPIRE_DAYS: int = 7
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Optional bootstrap values used only by scripts/seed_initial_data.py
    SEED_ADMIN_EMAIL: str = "admin@aiesecbardo.org"
    SEED_ADMIN_PASSWORD: str = "change-me-immediately"
    SEED_ADMIN_NAME: str = "SHIFT Admin"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    @field_validator("DATABASE_URL")
@classmethod
def normalize_database_url(cls, v: str) -> str:
    """Render hands out a connection string starting with postgres:// or
    plain postgresql://. psycopg2 understands both, but SQLAlchemy's dialect
    loader needs +psycopg2 spelled out explicitly."""
    if v.startswith("postgres://"):
        return v.replace("postgres://", "postgresql+psycopg2://", 1)
    if v.startswith("postgresql://") and "+psycopg2" not in v:
        return v.replace("postgresql://", "postgresql+psycopg2://", 1)
    return v

@property
def allowed_origins_list(self) -> List[str]:
    return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()
