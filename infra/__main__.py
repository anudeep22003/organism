"""StoryEngine infrastructure — dev stack."""

import pulumi

from components.iam import create_localhost_sa
from components.registry import create_docker_registry
from components.storage import BUCKET_NAME, create_media_bucket

# --- Layer 1: Storage ---
bucket = create_media_bucket()

# --- Layer 2: IAM ---
localhost_sa = create_localhost_sa(bucket)

# --- Layer 3: Artifact Registry ---
registry, registry_url = create_docker_registry()

# --- Stack outputs ---
# Readable via: pulumi stack output <key>
pulumi.export("bucket_name", BUCKET_NAME)
pulumi.export("service_account_email", localhost_sa.email)
pulumi.export("registry_url", registry_url)
