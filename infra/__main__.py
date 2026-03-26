"""StoryEngine infrastructure — dev stack."""

import pulumi

from components.cloudrun import create_cloudrun_service
from components.iam import create_cloudrun_sa, create_localhost_sa
from components.registry import create_docker_registry
from components.secrets import create_app_secrets
from components.storage import BUCKET_NAME, create_media_bucket

# --- Layer 1: Storage ---
bucket = create_media_bucket()

# --- Layer 2: IAM (localhost) ---
localhost_sa = create_localhost_sa(bucket)

# --- Layer 3: Artifact Registry ---
registry, registry_url = create_docker_registry()

# --- Layer 4: Secrets ---
secrets = create_app_secrets()

# --- Layer 5: IAM (Cloud Run) + Cloud Run service ---
cloudrun_sa = create_cloudrun_sa(bucket, registry, secrets)
service, service_url = create_cloudrun_service(cloudrun_sa, secrets, registry_url)

# --- Stack outputs ---
# Readable via: pulumi stack output <key>
pulumi.export("bucket_name", BUCKET_NAME)
pulumi.export("service_account_email", localhost_sa.email)
pulumi.export("registry_url", registry_url)
pulumi.export("secret_anthropic_api_key", secrets.anthropic_api_key.secret_id)
pulumi.export("secret_openai_api_key", secrets.openai_api_key.secret_id)
pulumi.export("secret_fal_api_key", secrets.fal_api_key.secret_id)
pulumi.export("secret_database_url", secrets.database_url.secret_id)
pulumi.export("cloudrun_sa_email", cloudrun_sa.email)
pulumi.export("service_url", service_url)
