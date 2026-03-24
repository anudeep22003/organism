import pulumi_gcp as gcp


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
