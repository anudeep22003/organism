from typing import Any

from core.config import AppSettings


def _settings(**overrides: Any) -> AppSettings:
    values: dict[str, Any] = {
        "database_url": "postgresql+psycopg://user:pass@localhost:5432/db",
        "openai_api_key": "openai",
        "anthropic_api_key": "anthropic",
        "fal_api_key": "fal",
        "gcp_project_id": "project",
        "gcp_region": "region",
        "gcp_storage_bucket": "bucket",
        "google_oauth_client_secret": "google-secret",
        "jwt_secret_key": "jwt-secret",
        "auth_session_secret": "session-secret",
        "google_oauth_client_id": "google-client",
        "fernet_encryption_key": "fernet-key",
        "frontend_url": "http://localhost:5173",
        "api_url": "http://localhost:8080",
    }
    values.update(overrides)
    return AppSettings(**values)


def test_csrf_cookie_domain_defaults_to_host_only() -> None:
    assert _settings().csrf_cookie_domain is None


def test_csrf_cookie_domain_can_be_configured() -> None:
    settings = _settings(csrf_cookie_domain="dekatha.com")

    assert settings.csrf_cookie_domain == "dekatha.com"
