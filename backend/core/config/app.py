from pydantic_settings import SettingsConfigDict

from core.config.database import DatabaseSettings


class AppSettings(DatabaseSettings):
    """Full application settings. Instantiated once as a module-level singleton.

    Inherits database_url from DatabaseSettings. If any required var is missing,
    pydantic raises ValidationError immediately and the process refuses to start.

    pydantic-settings reads vars in this order (highest priority first):
      1. os.environ  (explicit environment variables — Cloud Run, CI)
      2. .env.local  (if it exists — local dev only, silently ignored if missing)
      3. Default values defined in this class

    This file is only imported by core/config/__init__.py, which is only imported
    by app code (not by alembic). So API key validation never runs in the migration
    job context.
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


# Module-level singleton — canonical FastAPI pattern.
# Validation runs here, at import time of this file.
# If a required var is missing, the process exits before serving any requests.
settings = AppSettings()  # type: ignore[call-arg]
