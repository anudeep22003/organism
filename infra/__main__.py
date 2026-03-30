"""StoryEngine infrastructure — main stack.

Refactor status: Round 2 complete (storage, registry, secrets, networking, iam).
Remaining: database, cloudrun, migrations, frontend, ci.
"""

import pulumi
import pulumi_gcp as gcp

from components.ci import create_ci_resources
from components.cloudrun import create_cloudrun_service
from components.config import MEDIA_BUCKET_NAME
from components.database import create_database
from components.frontend import create_frontend
from components.iam import CloudRunServiceAccount, LocalhostServiceAccount
from components.migrations import create_migration_job
from components.networking import Network
from components.registry import DockerRegistry
from components.secrets import AppSecrets
from components.storage import MediaBucket

# --- Layer 1: Storage ---
storage = MediaBucket("storage")

# --- Layer 2: IAM (localhost) ---
localhost_sa = LocalhostServiceAccount("localhost-sa", bucket=storage.bucket)

# --- Layer 3: Artifact Registry ---
registry = DockerRegistry("registry")

# --- Layer 4: Secrets ---
secrets = AppSecrets("secrets")

# --- Layer 5: IAM (Cloud Run) ---
cloudrun_sa = CloudRunServiceAccount(
    "cloudrun-sa",
    bucket=storage.bucket,
    registry=registry.repository,
    secrets=secrets,
)

# --- Layer 6: Networking ---
network = Network("network")

# --- Layer 7: Database ---
# network.peering_connection is passed explicitly so Pulumi knows to wait for
# the VPC peering to complete before creating the Cloud SQL instance.
db = create_database(network.vpc, network.peering_connection, secrets)

# Write the constructed DATABASE_URL to Secret Manager.
# This runs after Cloud SQL is created and its private IP is known.
# Cloud Run reads this secret at startup — it sees the final resolved
# connection string and never needs to know how it was constructed.
#
# SecretVersion creates a new version in the existing secret container
# (created in Layer 4 by secrets.py). If the URL changes (e.g. instance
# is recreated with a new IP), pulumi up writes a new version automatically.
#
# This resource lives in __main__.py intentionally — it depends on BOTH
# db.database_url (from Database) and secrets.database_url.id (from AppSecrets).
# It's a cross-component wiring step that belongs at the orchestration level.
gcp.secretmanager.SecretVersion(
    "database-url-version",
    secret=secrets.database_url.id,
    secret_data=db.database_url,
)

# --- Layer 8a: Cloud Run service — wired after networking + db ---
service, service_url = create_cloudrun_service(
    cloudrun_sa.account, secrets, registry.url, network.vpc, network.subnet
)

# --- Layer 9: Migration Job ---
# Runs alembic upgrade head inside the VPC using the same image as the service.
# Triggered via: make migrate (or gcloud run jobs execute in CI)
migration_job = create_migration_job(
    cloudrun_sa.account, secrets, registry.url, network.vpc, network.subnet
)

# --- Layer 8b: Frontend hosting ---
# service is passed so the LB can create a Serverless NEG pointing at the
# Cloud Run service — routing api.dekatha.com through the same LB as the frontend.
frontend = create_frontend(service)

# --- Layer 10: CI/CD (Workload Identity + github-actions-sa) ---
ci = create_ci_resources(registry.repository, cloudrun_sa.account, frontend.bucket)

# --- Stack outputs ---
# Readable via: pulumi stack output <key>
pulumi.export("bucket_name", MEDIA_BUCKET_NAME)
pulumi.export("service_account_email", localhost_sa.email)
pulumi.export("registry_url", registry.url)
pulumi.export("secret_anthropic_api_key", secrets.anthropic_api_key.secret_id)
pulumi.export("secret_openai_api_key", secrets.openai_api_key.secret_id)
pulumi.export("secret_fal_api_key", secrets.fal_api_key.secret_id)
pulumi.export("secret_database_url", secrets.database_url.secret_id)
pulumi.export("cloudrun_sa_email", cloudrun_sa.email)
pulumi.export("service_url", service_url)
pulumi.export("vpc_name", network.vpc.name)
pulumi.export("subnet_name", network.subnet.name)
pulumi.export("db_instance_name", db.instance.name)
pulumi.export("db_private_ip", db.instance.private_ip_address)
pulumi.export("frontend_bucket", frontend.bucket.name)
pulumi.export("frontend_ip", frontend.ip_address)
pulumi.export("frontend_url", frontend.url)
pulumi.export("api_url", frontend.api_url)
pulumi.export("migration_job_name", migration_job.name)
pulumi.export("workload_identity_provider", ci.provider_name)
pulumi.export("github_actions_sa_email", ci.sa_email)
