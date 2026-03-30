"""
IAM component — service accounts and permission bindings.

Two separate ComponentResource classes:
  - LocalhostServiceAccount: the SA used when running the app locally
  - CloudRunServiceAccount: the SA the Cloud Run container runs as

They are separate because they have different dependencies and different
use cases. A future project might want LocalhostServiceAccount without
CloudRunServiceAccount.

Usage:
    # Layer 2 — depends only on storage
    localhost_sa = LocalhostServiceAccount("localhost-sa", bucket=storage.bucket)
    localhost_sa.account   # gcp.serviceaccount.Account
    localhost_sa.email     # pulumi.Output[str]

    # Layer 5 — depends on storage, registry, secrets
    cloudrun_sa = CloudRunServiceAccount(
        "cloudrun-sa",
        bucket=storage.bucket,
        registry=registry.repository,
        secrets=secrets,
    )
    cloudrun_sa.account    # gcp.serviceaccount.Account
    cloudrun_sa.email      # pulumi.Output[str]

Attributes exposed:
    LocalhostServiceAccount:
        account (gcp.serviceaccount.Account): the service account resource
        email   (pulumi.Output[str]): the service account email

    CloudRunServiceAccount:
        account (gcp.serviceaccount.Account): the service account resource
        email   (pulumi.Output[str]): the service account email

Design decisions:
    - Bindings are per-resource (not project-wide) wherever possible — least privilege.
    - cloudrun-sa gets secretAccessor per-secret, not project-wide.
    - roles/cloudsql.client is necessarily project-level — Cloud SQL IAM works
      at the project level, not per-instance.
    - No JSON key for cloudrun-sa — GCP attaches the identity to the container
      automatically. localhost-sa downloads a key separately (not managed here).

To add a new secret binding to CloudRunServiceAccount:
    Add a new SecretIamMember in CloudRunServiceAccount.__init__:
        gcp.secretmanager.SecretIamMember(
            f"{name}-<secret-name>-accessor",
            secret_id=secrets.<new_secret>.secret_id,
            role="roles/secretmanager.secretAccessor",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )
    See AGENT.md for the full step-by-step.
"""

import pulumi
import pulumi_gcp as gcp

from components.config import APP, PROJECT
from components.secrets import AppSecrets


class LocalhostServiceAccount(pulumi.ComponentResource):
    """
    Service account for local development.

    localhost-sa is the identity used when code runs on a developer's
    local machine. Its JSON key is downloaded separately and pointed to
    via GOOGLE_APPLICATION_CREDENTIALS.

    Permissions granted:
        roles/storage.objectUser on the media bucket:
            storage.objects.create  → upload blobs
            storage.objects.get     → read blobs + generate signed URLs
            storage.objects.list    → list blobs (used in test cleanup)
            storage.objects.delete  → delete blobs (used in test cleanup)

    Child resources (all parented to this component):
        {name}-account          gcp.serviceaccount.Account
        {name}-object-user      gcp.storage.BucketIAMMember
    """

    account: gcp.serviceaccount.Account
    email: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        bucket: gcp.storage.Bucket,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:LocalhostServiceAccount", name, {}, opts)

        self.account = gcp.serviceaccount.Account(
            f"{name}-account",
            account_id="localhost-sa",
            display_name="Localhost Service Account",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.email = self.account.email

        gcp.storage.BucketIAMMember(
            f"{name}-object-user",
            bucket=bucket.name,
            role="roles/storage.objectUser",
            member=self.account.email.apply(lambda e: f"serviceAccount:{e}"),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "account": self.account,
                "email": self.email,
            }
        )


class CloudRunServiceAccount(pulumi.ComponentResource):
    """
    Service account for the Cloud Run backend service.

    cloudrun-sa is the identity the Cloud Run container runs as. Unlike
    localhost-sa it never uses a JSON key — GCP attaches the identity to
    the container automatically via Workload Identity. No key file exists.

    Permissions granted:
        roles/artifactregistry.reader on the registry repository
            Cloud Run pulls the Docker image at startup. Without this
            the pull fails and the revision never boots.

        roles/secretmanager.secretAccessor per secret (not project-wide)
            Cloud Run fetches secret values and injects them as env vars
            before your code starts. Binding per-secret — least privilege.

        roles/storage.objectUser on the media bucket
            Upload images, read blobs, generate signed URLs at runtime.

        roles/cloudsql.client (project-level)
            Cloud SQL IAM works at the project level. Grants network-level
            access — "allowed to knock on the door". Still requires valid
            DB credentials for the actual connection.

    Child resources (all parented to this component):
        {name}-account                  gcp.serviceaccount.Account
        {name}-ar-reader                gcp.artifactregistry.RepositoryIamMember
        {name}-anthropic-accessor       gcp.secretmanager.SecretIamMember
        {name}-openai-accessor          gcp.secretmanager.SecretIamMember
        {name}-fal-accessor             gcp.secretmanager.SecretIamMember
        {name}-database-accessor        gcp.secretmanager.SecretIamMember
        {name}-object-user              gcp.storage.BucketIAMMember
        {name}-cloudsql-client          gcp.projects.IAMMember
    """

    account: gcp.serviceaccount.Account
    email: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        bucket: gcp.storage.Bucket,
        registry: gcp.artifactregistry.Repository,
        secrets: AppSecrets,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:CloudRunServiceAccount", name, {}, opts)

        self.account = gcp.serviceaccount.Account(
            f"{name}-account",
            account_id="cloudrun-sa",
            display_name="Cloud Run Service Account",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.email = self.account.email

        member = self.account.email.apply(lambda e: f"serviceAccount:{e}")

        # --- Artifact Registry: pull the Docker image at startup ---
        gcp.artifactregistry.RepositoryIamMember(
            f"{name}-ar-reader",
            repository=registry.name,
            location=registry.location,
            project=registry.project,
            role="roles/artifactregistry.reader",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # --- Secret Manager: read each secret value at startup ---
        # Bound per-secret, not project-wide — least privilege.
        gcp.secretmanager.SecretIamMember(
            f"{name}-anthropic-accessor",
            secret_id=secrets.anthropic_api_key.secret_id,
            role="roles/secretmanager.secretAccessor",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        gcp.secretmanager.SecretIamMember(
            f"{name}-openai-accessor",
            secret_id=secrets.openai_api_key.secret_id,
            role="roles/secretmanager.secretAccessor",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        gcp.secretmanager.SecretIamMember(
            f"{name}-fal-accessor",
            secret_id=secrets.fal_api_key.secret_id,
            role="roles/secretmanager.secretAccessor",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        gcp.secretmanager.SecretIamMember(
            f"{name}-database-accessor",
            secret_id=secrets.database_url.secret_id,
            role="roles/secretmanager.secretAccessor",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # --- GCS: read/write blobs and generate signed URLs at runtime ---
        gcp.storage.BucketIAMMember(
            f"{name}-object-user",
            bucket=bucket.name,
            role="roles/storage.objectUser",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # --- Cloud SQL: allow the SA to open connections to any Cloud SQL
        # instance in the project. Project-level because Cloud SQL IAM
        # works at the project level. Grants network-level access only —
        # a valid username + password is still required for the session.
        gcp.projects.IAMMember(
            f"{name}-cloudsql-client",
            project=PROJECT,
            role="roles/cloudsql.client",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "account": self.account,
                "email": self.email,
            }
        )
