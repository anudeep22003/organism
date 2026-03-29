from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Minimal settings for alembic migrations — only DATABASE_URL required.

    This class is deliberately separate from AppSettings so that alembic/env.py
    can import it without triggering AppSettings instantiation (which validates
    API keys that the migration job doesn't have).

    Import path for alembic:
        from core.config.database import DatabaseSettings

    This bypasses core/config/__init__.py entirely, so app.py is never imported
    and AppSettings() is never called.

    pydantic-settings silently ignores a missing .env.local file, so this is
    safe to instantiate in any environment that only has DATABASE_URL set.
    """

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_ignore_empty=True,
        extra="ignore",
    )
