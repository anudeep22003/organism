import pulumi_gcp as gcp

from components.secrets import AppSecrets


def create_localhost_sa(bucket: gcp.storage.Bucket) -> gcp.serviceaccount.Account:
    """
    Creates a service account for localhost development and grants it
    the minimum permissions needed to operate on the media bucket.

    localhost-sa is the identity used when code runs on a developer's local machine.
    Its JSON key is downloaded separately and pointed to via GOOGLE_APPLICATION_CREDENTIALS.

    Permissions granted:
    - roles/storage.objectUser on the media bucket:
        storage.objects.create  → upload blobs
        storage.objects.get     → read blobs + generate signed URLs
        storage.objects.list    → list blobs (used in test cleanup)
        storage.objects.delete  → delete blobs (used in test cleanup)
    """
    sa = gcp.serviceaccount.Account(
        "localhost-sa",
        account_id="localhost-sa",
        display_name="Localhost Service Account",
    )

    gcp.storage.BucketIAMMember(
        "localhost-sa-object-user",
        bucket=bucket.name,
        role="roles/storage.objectUser",
        member=sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

    return sa


def create_cloudrun_sa(
    bucket: gcp.storage.Bucket,
    registry: gcp.artifactregistry.Repository,
    secrets: AppSecrets,
) -> gcp.serviceaccount.Account:
    """
    Creates a service account for the Cloud Run backend service and grants
    it the minimum permissions needed to start up and operate.

    cloudrun-sa is the identity the Cloud Run container runs as. Unlike
    localhost-sa it never uses a JSON key — GCP attaches the identity to
    the container automatically via Workload Identity. No key file exists.

    Permissions granted:

    1. roles/artifactregistry.reader on the registry repository
       Cloud Run pulls the Docker image at startup. Without this the
       pull fails and the revision never boots.

    2. roles/secretmanager.secretAccessor on each individual secret
       Cloud Run fetches secret values and injects them as env vars
       before your code starts. Binding per-secret, not project-wide,
       so this SA can only read exactly the secrets it needs.

    3. roles/storage.objectUser on the media bucket
       Same GCS operations as localhost-sa — upload images, read blobs,
       generate signed URLs. The bucket doesn't care which SA writes to
       it, both identities get the same role independently.
    """
    sa = gcp.serviceaccount.Account(
        "cloudrun-sa",
        account_id="cloudrun-sa",
        display_name="Cloud Run Service Account",
    )

    member = sa.email.apply(lambda email: f"serviceAccount:{email}")

    # --- Artifact Registry: pull the Docker image at startup ---
    gcp.artifactregistry.RepositoryIamMember(
        "cloudrun-sa-ar-reader",
        repository=registry.name,
        location=registry.location,
        project=registry.project,
        role="roles/artifactregistry.reader",
        member=member,
    )

    # --- Secret Manager: read each secret value at startup ---
    # Bound per-secret, not project-wide — least privilege.
    gcp.secretmanager.SecretIamMember(
        "cloudrun-sa-anthropic-accessor",
        secret_id=secrets.anthropic_api_key.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=member,
    )

    gcp.secretmanager.SecretIamMember(
        "cloudrun-sa-openai-accessor",
        secret_id=secrets.openai_api_key.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=member,
    )

    gcp.secretmanager.SecretIamMember(
        "cloudrun-sa-fal-accessor",
        secret_id=secrets.fal_api_key.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=member,
    )

    gcp.secretmanager.SecretIamMember(
        "cloudrun-sa-database-accessor",
        secret_id=secrets.database_url.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=member,
    )

    # --- GCS: read/write blobs and generate signed URLs at runtime ---
    gcp.storage.BucketIAMMember(
        "cloudrun-sa-object-user",
        bucket=bucket.name,
        role="roles/storage.objectUser",
        member=member,
    )

    return sa
