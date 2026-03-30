"""
Secret Manager component.

Creates Secret Manager secret containers (slots) for all app secrets.
Pulumi creates the slot but never writes the value — secrets are populated
separately via `make populate-secrets` so plaintext never enters Pulumi state
or git history.

Usage:
    secrets = AppSecrets("secrets")
    # Access individual secrets:
    secrets.anthropic_api_key  # gcp.secretmanager.Secret
    secrets.openai_api_key     # gcp.secretmanager.Secret
    secrets.fal_api_key        # gcp.secretmanager.Secret
    secrets.database_url       # gcp.secretmanager.Secret
    secrets.db_password        # gcp.secretmanager.Secret

Attributes exposed:
    anthropic_api_key (gcp.secretmanager.Secret): Anthropic API key slot
    openai_api_key    (gcp.secretmanager.Secret): OpenAI API key slot
    fal_api_key       (gcp.secretmanager.Secret): Fal.ai API key slot
    database_url      (gcp.secretmanager.Secret): DATABASE_URL slot (value
                      written by Pulumi after DB is created — do not populate
                      manually via make populate-secrets)
    db_password       (gcp.secretmanager.Secret): DB password slot (value
                      written by Pulumi's random.RandomPassword in database.py)

Design decisions:
    - Replication is set to automatic — GCP manages redundancy across regions.
      For a single-region setup this is the simplest correct choice.
    - Pulumi creates the slot; populate-secrets.sh writes the values. This
      keeps plaintext out of Pulumi state and git history.
    - DATABASE_URL and db_password are owned entirely by Pulumi — never
      manually populate them. See database.py for how values are written.

To add a new secret:
    1. Add a new _make_secret() call in __init__ below.
    2. Grant cloudrun-sa access in iam.py (CloudRunServiceAccount).
    3. Mount it in cloudrun.py (CloudRunService) via secret_env_vars.
    4. Run: make up && make populate-secrets
    See AGENT.md for the full step-by-step.
"""

import pulumi
import pulumi_gcp as gcp

from components.config import APP, PREFIX


def _make_secret(
    logical_name: str,
    secret_id: str,
    parent: pulumi.Resource,
) -> gcp.secretmanager.Secret:
    """
    Creates a named secret container in Secret Manager.

    This creates the SLOT — not the value. The value is populated separately
    via the populate-secrets.sh script (or by Pulumi for auto-generated
    credentials like db_password and database_url).

    Args:
        logical_name: Pulumi logical name for this resource (component-scoped).
        secret_id: The GCP secret ID (shown in the console and gcloud).
        parent: The ComponentResource that owns this secret (for Pulumi graph).
    """
    return gcp.secretmanager.Secret(
        logical_name,
        secret_id=secret_id,
        replication=gcp.secretmanager.SecretReplicationArgs(
            auto=gcp.secretmanager.SecretReplicationAutoArgs(),
        ),
        opts=pulumi.ResourceOptions(parent=parent),
    )


class AppSecrets(pulumi.ComponentResource):
    """
    Secret Manager containers for all app secrets.

    Creates the secret slots only — values are populated separately so
    plaintext credentials never enter Pulumi state or git history.

    Passed to CloudRunServiceAccount (for IAM bindings), Database (for
    db_password slot), and CloudRunService (for secret env var references).

    Child resources (all parented to this component):
        {name}-anthropic-api-key   gcp.secretmanager.Secret
        {name}-openai-api-key      gcp.secretmanager.Secret
        {name}-fal-api-key         gcp.secretmanager.Secret
        {name}-database-url        gcp.secretmanager.Secret
        {name}-db-password         gcp.secretmanager.Secret
    """

    anthropic_api_key: gcp.secretmanager.Secret
    openai_api_key: gcp.secretmanager.Secret
    fal_api_key: gcp.secretmanager.Secret
    database_url: gcp.secretmanager.Secret
    db_password: gcp.secretmanager.Secret

    def __init__(
        self,
        name: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:AppSecrets", name, {}, opts)

        self.anthropic_api_key = _make_secret(
            f"{name}-anthropic-api-key",
            f"{PREFIX}-anthropic-api-key",
            parent=self,
        )
        self.openai_api_key = _make_secret(
            f"{name}-openai-api-key",
            f"{PREFIX}-openai-api-key",
            parent=self,
        )
        self.fal_api_key = _make_secret(
            f"{name}-fal-api-key",
            f"{PREFIX}-fal-api-key",
            parent=self,
        )
        self.database_url = _make_secret(
            f"{name}-database-url",
            f"{PREFIX}-database-url",
            parent=self,
        )
        # db_password is managed entirely by Pulumi — generated randomly by
        # database.py, stored here so it's retrievable via gcloud if needed
        # (e.g. make migrate reads it). The app never reads this directly;
        # it reads DATABASE_URL instead.
        self.db_password = _make_secret(
            f"{name}-db-password",
            f"{PREFIX}-db-password",
            parent=self,
        )

        self.register_outputs(
            {
                "anthropic_api_key": self.anthropic_api_key,
                "openai_api_key": self.openai_api_key,
                "fal_api_key": self.fal_api_key,
                "database_url": self.database_url,
                "db_password": self.db_password,
            }
        )
