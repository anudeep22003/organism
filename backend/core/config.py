from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Full application settings. Instantiated once as a module-level singleton.

    pydantic-settings reads vars in this order (highest priority first):
      1. os.environ  — explicit environment variables (Cloud Run, CI)
      2. .env.local  — local dev only, silently ignored if missing
      3. Default values defined in this class

    If any required var is missing, pydantic raises ValidationError immediately
    and the process refuses to start — fail fast before accepting any traffic.

    Note: alembic/env.py reads DATABASE_URL directly from os.environ and never
    imports this module. That is intentional — the migration job only has
    DATABASE_URL; importing settings here would fail validation in that context.
    """

    database_url: str
    openai_api_key: str
    anthropic_api_key: str
    fal_api_key: str
    gcp_project_id: str
    gcp_region: str
    gcp_storage_bucket: str
    # Optional — only needed locally for GCS access outside Cloud Run.
    # Cloud Run services authenticate via the attached service account (no key file).
    google_application_credentials: str = ""

    # Deployment environment. Controls whether API docs are exposed.
    # Set to "production" via plain env var in Cloud Run (cloudrun.py).
    # Defaults to "development" locally — docs available at /docs.
    env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = AppSettings()  # type: ignore[call-arg]
