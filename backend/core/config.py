from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Minimal settings for alembic migrations — only DATABASE_URL required.

    Used directly by alembic/env.py so migrations work without API keys present.
    pydantic-settings silently ignores a missing .env.local file, so this is
    safe to instantiate in any environment that has DATABASE_URL set.
    """

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_ignore_empty=True,
        extra="ignore",
    )


class AppSettings(DatabaseSettings):
    """Full application settings. Instantiated once as a module-level singleton.

    If any required var is missing, pydantic raises ValidationError immediately
    and the process refuses to start — fail fast before accepting any traffic.

    pydantic-settings reads vars in this order (highest priority first):
      1. os.environ (explicit environment variables — Cloud Run, CI)
      2. .env.local file (if it exists — local dev only)
      3. Default values defined in this class

    The .env.local file is silently ignored if missing (Cloud Run, CI).
    No conditional load_dotenv() needed — pydantic-settings handles it.

    Alembic imports DatabaseSettings directly — it never touches this class,
    so API key validation never runs during migrations regardless of what env
    vars are present in the migration environment.
    """

    openai_api_key: str
    anthropic_api_key: str
    fal_api_key: str
    gcp_project_id: str
    gcp_region: str
    gcp_storage_bucket: str
    # Optional — only needed locally for GCS access outside Cloud Run.
    # Cloud Run services authenticate via the attached service account (no key file).
    google_application_credentials: str = ""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_ignore_empty=True,
        extra="ignore",
    )


# Module-level singleton — the canonical FastAPI pattern (per official docs and
# the FastAPI full-stack template). Validation runs here, at import time.
# If a required var is missing, the process exits before serving any requests.
#
# Alembic uses DatabaseSettings() directly — it never imports `settings`,
# so this line is never executed in the migration job context.
settings = AppSettings()  # type: ignore[call-arg]
