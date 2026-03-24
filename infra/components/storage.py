import pulumi_gcp as gcp

BUCKET_NAME = "storyengine-dev-media-x7k2"


def create_media_bucket() -> gcp.storage.Bucket:
    """
    Creates the GCS bucket that stores all media for the storyengine dev environment.

    - uniform_bucket_level_access: disables per-object ACLs, all access is
      controlled purely through IAM bindings. Cleaner and more auditable.
    - public_access_prevention: enforced means no one can ever make this bucket
      or its objects public, even accidentally. All access goes through signed URLs.
    """
    bucket = gcp.storage.Bucket(
        "media-bucket",
        name=BUCKET_NAME,
        location="europe-west2",
        uniform_bucket_level_access=True,
        public_access_prevention="enforced",
    )

    return bucket
