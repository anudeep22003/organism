"""
CI/CD infrastructure — Workload Identity Federation + github-actions-sa.

Provisions the GCP-side resources that allow GitHub Actions to authenticate
to GCP without a JSON key file. GitHub generates a short-lived OIDC token
per workflow run; GCP exchanges it for a temporary access token scoped to
github-actions-sa. The token expires when the workflow ends.

Usage:
    ci = CiResources(
        "ci",
        registry=registry.repository,
        cloudrun_sa=cloudrun_sa.account,
        frontend_bucket=frontend.bucket,
    )
    ci.sa_email       # pulumi.Output[str] — github-actions-sa email
    ci.provider_name  # pulumi.Output[str] — WIF provider resource name

Attributes exposed:
    sa_email      (pulumi.Output[str]): github-actions-sa email address
                  → GCP_SERVICE_ACCOUNT GitHub Actions secret
    provider_name (pulumi.Output[str]): full WIF provider resource name
                  format: projects/<n>/locations/global/workloadIdentityPools/<pool>/providers/<provider>
                  → GCP_WORKLOAD_IDENTITY_PROVIDER GitHub Actions secret

After running pulumi up, copy these two outputs to GitHub:
    Settings → Secrets and variables → Actions:
        GCP_WORKLOAD_IDENTITY_PROVIDER  ← workload_identity_provider output
        GCP_SERVICE_ACCOUNT             ← github_actions_sa_email output

Design decisions:
    - Workload Identity Federation: no JSON keys. The OIDC token is scoped to
      the specific GitHub repo via attribute_condition — tokens from any other
      repo are rejected at the GCP gate.
    - roles/editor for github-actions-sa is intentional: Pulumi manages 10+
      resource types. Enumerating individual roles is high-maintenance and
      breaks when new resource types are added. roles/editor excludes IAM
      permissions — the SA cannot escalate its own privileges.
    - IAM bindings are per-resource where possible (registry, frontend bucket,
      cloudrun-sa user) — project-level only for run.developer and editor.
"""

import pulumi
import pulumi_gcp as gcp

from components.config import APP, GITHUB_REPO, PROJECT

# The GitHub repository that is allowed to authenticate via this pool.
# Read from Pulumi config (github_repo key) — set per stack in Pulumi.<stack>.yaml.
# Tokens from any other repo are rejected by the attribute_condition.
_GITHUB_REPO = GITHUB_REPO


class CiResources(pulumi.ComponentResource):
    """
    Service account and Workload Identity resources for CI/CD.

    Creates the github-actions-sa with minimum permissions for the deploy
    pipeline, plus the Workload Identity Pool and OIDC provider that allow
    GitHub Actions to authenticate without a JSON key.

    Child resources (all parented to this component):
        {name}-sa                       gcp.serviceaccount.Account
        {name}-ar-writer                gcp.artifactregistry.RepositoryIamMember
        {name}-run-developer            gcp.projects.IAMMember
        {name}-frontend-objectadmin     gcp.storage.BucketIAMMember
        {name}-cloudrun-sa-user         gcp.serviceaccount.IAMMember
        {name}-editor                   gcp.projects.IAMMember
        {name}-pool                     gcp.iam.WorkloadIdentityPool
        {name}-provider                 gcp.iam.WorkloadIdentityPoolProvider
        {name}-wi-binding               gcp.serviceaccount.IAMMember
    """

    sa_email: pulumi.Output[str]
    provider_name: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        registry: gcp.artifactregistry.Repository,
        cloudrun_sa: gcp.serviceaccount.Account,
        frontend_bucket: gcp.storage.Bucket,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:CiResources", name, {}, opts)

        # ── Service Account ────────────────────────────────────────────────────

        sa = gcp.serviceaccount.Account(
            f"{name}-sa",
            account_id="github-actions-sa",
            display_name="GitHub Actions CI/CD",
            description="Used by GitHub Actions to build, push, and deploy via Workload Identity",
            opts=pulumi.ResourceOptions(parent=self),
        )

        member = sa.email.apply(lambda email: f"serviceAccount:{email}")

        # ── IAM Bindings ──────────────────────────────────────────────────────

        # Push Docker images to Artifact Registry during the deploy job.
        gcp.artifactregistry.RepositoryIamMember(
            f"{name}-ar-writer",
            repository=registry.name,
            location=registry.location,
            project=registry.project,
            role="roles/artifactregistry.writer",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Update Cloud Run services and trigger Cloud Run Jobs (migrate step).
        gcp.projects.IAMMember(
            f"{name}-run-developer",
            project=PROJECT,
            role="roles/run.developer",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Sync built frontend assets to the GCS bucket.
        gcp.storage.BucketIAMMember(
            f"{name}-frontend-objectadmin",
            bucket=frontend_bucket.name,
            role="roles/storage.objectAdmin",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Allow Pulumi to deploy Cloud Run services that run as cloudrun-sa.
        # Without this, Pulumi cannot set service_account on the Cloud Run resource.
        gcp.serviceaccount.IAMMember(
            f"{name}-cloudrun-sa-user",
            service_account_id=cloudrun_sa.name,
            role="roles/iam.serviceAccountUser",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Broad project-level permission for Pulumi to manage all stack resources.
        # roles/editor does not include IAM permissions — that's intentional.
        # This is the standard pattern for CI service accounts running IaC tools.
        gcp.projects.IAMMember(
            f"{name}-editor",
            project=PROJECT,
            role="roles/editor",
            member=member,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ── Workload Identity Pool ─────────────────────────────────────────────

        pool = gcp.iam.WorkloadIdentityPool(
            f"{name}-pool",
            workload_identity_pool_id="github-actions-pool",
            display_name="GitHub Actions",
            description="Workload Identity pool for GitHub Actions OIDC authentication",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ── OIDC Provider ─────────────────────────────────────────────────────

        provider = gcp.iam.WorkloadIdentityPoolProvider(
            f"{name}-provider",
            workload_identity_pool_id=pool.workload_identity_pool_id,
            workload_identity_pool_provider_id="github-actions-provider",
            display_name="GitHub Actions OIDC",
            description="OIDC provider for GitHub Actions — scoped to the organism repo",
            oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
                issuer_uri="https://token.actions.githubusercontent.com",
            ),
            attribute_mapping={
                "google.subject": "assertion.sub",
                "attribute.repository": "assertion.repository",
                "attribute.ref": "assertion.ref",
                "attribute.actor": "assertion.actor",
            },
            # Tokens from any repo other than this one are rejected at the GCP gate.
            # This is the primary security boundary — even a leaked workflow token
            # from a different repo cannot impersonate github-actions-sa.
            attribute_condition=f'attribute.repository == "{_GITHUB_REPO}"',
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ── WIF → SA Binding ─────────────────────────────────────────────────
        # Allows principals authenticated via this pool (i.e. GitHub Actions runs
        # from the organism repo) to impersonate github-actions-sa.

        gcp.serviceaccount.IAMMember(
            f"{name}-wi-binding",
            service_account_id=sa.name,
            role="roles/iam.workloadIdentityUser",
            member=pool.name.apply(
                lambda pool_name: (
                    f"principalSet://iam.googleapis.com/{pool_name}"
                    f"/attribute.repository/{_GITHUB_REPO}"
                )
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.sa_email = sa.email
        self.provider_name = provider.name

        self.register_outputs(
            {
                "sa_email": self.sa_email,
                "provider_name": self.provider_name,
            }
        )
