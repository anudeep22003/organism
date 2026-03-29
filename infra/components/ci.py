"""
CI/CD infrastructure — Workload Identity Federation + github-actions-sa.

This module provisions the GCP-side resources that allow GitHub Actions to
authenticate to GCP without a JSON key file. GitHub generates a short-lived
OIDC token per workflow run; GCP exchanges it for a temporary access token
scoped to github-actions-sa. The token expires when the workflow ends.

Resources created:
  - github-actions-sa           service account that CI runs as
  - IAM bindings                minimum permissions for the deploy pipeline
  - github-actions-pool         Workload Identity Pool
  - github-actions-provider     OIDC provider, scoped to this repo only
  - WIF → SA binding            allows the pool to impersonate the SA

After running `pulumi up --stack main`, copy the two stack outputs to GitHub:
  Settings → Secrets and variables → Actions:
    GCP_WORKLOAD_IDENTITY_PROVIDER  ← workload_identity_provider output
    GCP_SERVICE_ACCOUNT             ← github_actions_sa_email output
"""

import pulumi
import pulumi_gcp as gcp

from components.config import PROJECT, REGION, resource_name

# The GitHub repository that is allowed to authenticate via this pool.
# Tokens from any other repo are rejected by the attribute_condition.
_GITHUB_REPO = "anudeep22003/organism"


class CiOutputs:
    def __init__(
        self,
        sa_email: pulumi.Output[str],
        provider_name: pulumi.Output[str],
    ) -> None:
        self.sa_email = sa_email
        self.provider_name = provider_name


def create_ci_resources(
    registry: gcp.artifactregistry.Repository,
    cloudrun_sa: gcp.serviceaccount.Account,
    frontend_bucket: gcp.storage.Bucket,
) -> CiOutputs:
    """
    Creates the service account and Workload Identity resources for CI/CD.

    Parameters
    ----------
    registry:
        The Artifact Registry repository. github-actions-sa needs
        artifactregistry.writer here to push built Docker images.
    cloudrun_sa:
        The Cloud Run service account. github-actions-sa needs
        iam.serviceAccountUser on this SA so that Pulumi can deploy
        Cloud Run services that run as cloudrun-sa.
    frontend_bucket:
        The GCS bucket serving the frontend. github-actions-sa needs
        storage.objectAdmin here to sync built frontend assets.
    """

    # ── Service Account ────────────────────────────────────────────────────────

    sa = gcp.serviceaccount.Account(
        "github-actions-sa",
        account_id="github-actions-sa",
        display_name="GitHub Actions CI/CD",
        description="Used by GitHub Actions to build, push, and deploy via Workload Identity",
    )

    member = sa.email.apply(lambda email: f"serviceAccount:{email}")

    # ── IAM Bindings ───────────────────────────────────────────────────────────

    # Push Docker images to Artifact Registry during the deploy job.
    gcp.artifactregistry.RepositoryIamMember(
        "github-actions-sa-ar-writer",
        repository=registry.name,
        location=registry.location,
        project=registry.project,
        role="roles/artifactregistry.writer",
        member=member,
    )

    # Update Cloud Run services and trigger Cloud Run Jobs (migrate step).
    gcp.projects.IAMMember(
        "github-actions-sa-run-developer",
        project=PROJECT,
        role="roles/run.developer",
        member=member,
    )

    # Sync built frontend assets to the GCS bucket.
    gcp.storage.BucketIAMMember(
        "github-actions-sa-frontend-objectadmin",
        bucket=frontend_bucket.name,
        role="roles/storage.objectAdmin",
        member=member,
    )

    # Allow Pulumi to deploy Cloud Run services that run as cloudrun-sa.
    # Without this, Pulumi cannot set service_account on the Cloud Run resource.
    gcp.serviceaccount.IAMMember(
        "github-actions-sa-cloudrun-sa-user",
        service_account_id=cloudrun_sa.name,
        role="roles/iam.serviceAccountUser",
        member=member,
    )

    # Broad project-level permission for Pulumi to manage all stack resources.
    # roles/editor does not include IAM permissions — that's intentional.
    # This is the standard pattern for CI service accounts running IaC tools.
    gcp.projects.IAMMember(
        "github-actions-sa-editor",
        project=PROJECT,
        role="roles/editor",
        member=member,
    )

    # ── Workload Identity Pool ─────────────────────────────────────────────────

    pool = gcp.iam.WorkloadIdentityPool(
        "github-actions-pool",
        workload_identity_pool_id="github-actions-pool",
        display_name="GitHub Actions",
        description="Workload Identity pool for GitHub Actions OIDC authentication",
    )

    # ── OIDC Provider ──────────────────────────────────────────────────────────

    provider = gcp.iam.WorkloadIdentityPoolProvider(
        "github-actions-provider",
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
    )

    # ── WIF → SA Binding ──────────────────────────────────────────────────────
    # Allows principals authenticated via this pool (i.e. GitHub Actions runs
    # from the organism repo) to impersonate github-actions-sa.

    gcp.serviceaccount.IAMMember(
        "github-actions-wi-binding",
        service_account_id=sa.name,
        role="roles/iam.workloadIdentityUser",
        member=pool.name.apply(
            lambda pool_name: (
                f"principalSet://iam.googleapis.com/{pool_name}"
                f"/attribute.repository/{_GITHUB_REPO}"
            )
        ),
    )

    # ── Provider resource name ─────────────────────────────────────────────────
    # The full provider resource name is what the GitHub Actions auth step
    # needs. Format: projects/<number>/locations/global/workloadIdentityPools/<pool>/providers/<provider>
    # pulumi_gcp exposes this as provider.name on the WorkloadIdentityPoolProvider resource.

    return CiOutputs(
        sa_email=sa.email,
        provider_name=provider.name,
    )
