import pulumi
import pulumi_gcp as gcp

# Secret names are prefixed with the stack name so they are
# unambiguous in the GCP project if more services are added later.
# e.g. storyengine-dev-anthropic-api-key
_PREFIX = "storyengine-dev"


def _make_secret(logical_name: str, secret_id: str) -> gcp.secretmanager.Secret:
    """
    Creates a named secret container in Secret Manager.

    This creates the SLOT — not the value. The value is populated separately
    via the populate-secrets.sh script. Pulumi never touches secret values,
    keeping plaintext credentials out of Pulumi state and git history.

    Replication is set to automatic, meaning GCP manages redundancy across
    regions within the project. For a single-region setup this is the
    simplest correct choice.
    """
    return gcp.secretmanager.Secret(
        logical_name,
        secret_id=secret_id,
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
    )


class AppSecrets:
    """
    Holds references to all Secret Manager secrets for the storyengine app.
    Passed to the Cloud Run component next layer so it can mount these
    secrets as environment variables without hardcoding secret IDs.
    """

    def __init__(self) -> None:
        self.anthropic_api_key = _make_secret(
            "secret-anthropic-api-key",
            f"{_PREFIX}-anthropic-api-key",
        )
        self.openai_api_key = _make_secret(
            "secret-openai-api-key",
            f"{_PREFIX}-openai-api-key",
        )
        self.fal_api_key = _make_secret(
            "secret-fal-api-key",
            f"{_PREFIX}-fal-api-key",
        )
        self.database_url = _make_secret(
            "secret-database-url",
            f"{_PREFIX}-database-url",
        )


def create_app_secrets() -> AppSecrets:
    return AppSecrets()
