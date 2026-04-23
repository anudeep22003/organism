"""
Secret Manager component.

Creates Secret Manager secret containers (slots) for all app secrets.
Pulumi creates the slot but never writes the value — secrets are populated
separately via `make populate-secrets` so plaintext never enters Pulumi state
or git history.

Usage:
    secrets = AppSecrets("secrets")
    # Infrastructure secrets (always present):
    secrets.database_url       # gcp.secretmanager.Secret
    secrets.db_password        # gcp.secretmanager.Secret
    # App secrets (StoryEngine-specific — replace with your own):
    secrets.anthropic_api_key  # gcp.secretmanager.Secret
    secrets.google_oauth_client_secret  # gcp.secretmanager.Secret
    secrets.jwt_secret_key     # gcp.secretmanager.Secret
    secrets.auth_session_secret  # gcp.secretmanager.Secret
    secrets.fernet_encryption_key  # gcp.secretmanager.Secret
    secrets.openai_api_key     # gcp.secretmanager.Secret
    secrets.fal_api_key        # gcp.secretmanager.Secret

Attributes exposed:
    database_url      (gcp.secretmanager.Secret): DATABASE_URL slot — value
                      written by Pulumi after DB is created. Never populate
                      manually via make populate-secrets.
    db_password       (gcp.secretmanager.Secret): DB password slot — value
                      written by Pulumi's random.RandomPassword in database.py.

    # StoryEngine-specific — replace with your own in a new project:
    anthropic_api_key (gcp.secretmanager.Secret): Anthropic API key slot
    google_oauth_client_secret (gcp.secretmanager.Secret): Google OAuth client secret slot
    jwt_secret_key    (gcp.secretmanager.Secret): JWT signing key slot
    auth_session_secret (gcp.secretmanager.Secret): Session middleware secret slot
    fernet_encryption_key (gcp.secretmanager.Secret): Fernet key slot for encrypted OAuth tokens
    openai_api_key    (gcp.secretmanager.Secret): OpenAI API key slot
    fal_api_key       (gcp.secretmanager.Secret): Fal.ai API key slot

Design decisions:
    - Replication is set to automatic — GCP manages redundancy across regions.
      For a single-region setup this is the simplest correct choice.
    - Pulumi creates the slot; populate-secrets.sh writes the values. This
      keeps plaintext out of Pulumi state and git history.
    - DATABASE_URL and db_password are owned entirely by Pulumi — never
      manually populate them. See database.py for how values are written.

New project — replace the app secrets:
    Delete the three StoryEngine secrets below and add your own.
    For each secret you add here, also add in iam.py and cloudrun.py.
    See AGENT.md for the full three-file pattern.

To add a new secret to an existing project:
    1. Add a new _make_secret() call in the app secrets section below.
    2. Grant cloudrun-sa access in iam.py → CloudRunServiceAccount.
    3. Mount it in cloudrun.py → CloudRunService via secret_env_vars.
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
        {name}-google-oauth-client-secret   gcp.secretmanager.Secret
        {name}-jwt-secret-key      gcp.secretmanager.Secret
        {name}-auth-session-secret gcp.secretmanager.Secret
        {name}-fernet-encryption-key gcp.secretmanager.Secret
        {name}-openai-api-key      gcp.secretmanager.Secret
        {name}-fal-api-key         gcp.secretmanager.Secret
        {name}-database-url        gcp.secretmanager.Secret
        {name}-db-password         gcp.secretmanager.Secret
    """

    anthropic_api_key: gcp.secretmanager.Secret
    google_oauth_client_secret: gcp.secretmanager.Secret
    jwt_secret_key: gcp.secretmanager.Secret
    auth_session_secret: gcp.secretmanager.Secret
    fernet_encryption_key: gcp.secretmanager.Secret
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

        # ── Infrastructure secrets — keep these, every project needs them ────────
        # Values are written by Pulumi (never by populate-secrets.sh).
        # Do not manually populate these — database.py owns both values.

        self.database_url = _make_secret(
            f"{name}-database-url",
            f"{PREFIX}-database-url",
            parent=self,
        )
        # db_password slot is written by database.py's RandomPassword.
        # The app never reads this directly — it reads DATABASE_URL which
        # embeds the password. Kept in Secret Manager so operators can
        # retrieve it manually (e.g. make proxy for DB inspection).
        self.db_password = _make_secret(
            f"{name}-db-password",
            f"{PREFIX}-db-password",
            parent=self,
        )

        # ── App secrets — replace these with your own ─────────────────────────
        # These three are StoryEngine-specific (Anthropic, OpenAI, Fal.ai).
        # When starting a new project:
        #   1. Delete these _make_secret() calls and add your own below.
        #   2. Delete the corresponding accessors in iam.py → CloudRunServiceAccount.
        #   3. Delete the corresponding env var mounts in cloudrun.py → CloudRunService.
        #   4. Add your own equivalents in all three places.
        #
        # To add a new secret (full guide in AGENT.md):
        #   self.my_secret = _make_secret(
        #       f"{name}-my-secret",       ← Pulumi logical name
        #       f"{PREFIX}-my-secret",     ← GCP Secret Manager secret_id
        #       parent=self,
        #   )

        self.anthropic_api_key = _make_secret(
            f"{name}-anthropic-api-key",
            f"{PREFIX}-anthropic-api-key",
            parent=self,
        )
        self.google_oauth_client_secret = _make_secret(
            f"{name}-google-oauth-client-secret",
            f"{PREFIX}-google-oauth-client-secret",
            parent=self,
        )
        self.jwt_secret_key = _make_secret(
            f"{name}-jwt-secret-key",
            f"{PREFIX}-jwt-secret-key",
            parent=self,
        )
        self.auth_session_secret = _make_secret(
            f"{name}-auth-session-secret",
            f"{PREFIX}-auth-session-secret",
            parent=self,
        )
        self.fernet_encryption_key = _make_secret(
            f"{name}-fernet-encryption-key",
            f"{PREFIX}-fernet-encryption-key",
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

        self.register_outputs(
            {
                "database_url": self.database_url,
                "db_password": self.db_password,
                # app secrets
                "anthropic_api_key": self.anthropic_api_key,
                "google_oauth_client_secret": self.google_oauth_client_secret,
                "jwt_secret_key": self.jwt_secret_key,
                "auth_session_secret": self.auth_session_secret,
                "fernet_encryption_key": self.fernet_encryption_key,
                "openai_api_key": self.openai_api_key,
                "fal_api_key": self.fal_api_key,
            }
        )
