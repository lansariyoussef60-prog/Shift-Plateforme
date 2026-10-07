from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Invite-based registration
    INVITE_EXPIRE_DAYS: int = 7
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Comma-separated list of origins allowed by CORS. Kept as a plain string
    # (not a list) because that's what a platform's env-var UI can set
    # directly — see allowed_origins_list below for the parsed form.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Optional bootstrap values used only by scripts/seed_initial_data.py
    SEED_ADMIN_EMAIL: str = "admin@aiesecbardo.org"
    SEED_ADMIN_PASSWORD: str = "change-me-immediately"
    SEED_ADMIN_NAME: str = "SHIFT Admin"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Managed Postgres providers (Render, Railway, Heroku-style) hand out
        a connection string starting with postgres:// or plain postgresql://.
        psycopg2 itself understands both, but SQLAlchemy's dialect loader
        needs the +psycopg2 driver suffix spelled out, so normalize it here
        rather than requiring a manual edit to whatever the platform gives you.
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://") and "+psycopg2" not in v:
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
