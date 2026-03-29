import pulumi_gcp as gcp

from components.config import IMAGE_TAG, REGION, resource_name
from components.secrets import AppSecrets


def create_migration_job(
    sa: gcp.serviceaccount.Account,
    secrets: AppSecrets,
    registry_url,
    vpc: gcp.compute.Network,
    subnet: gcp.compute.Subnetwork,
) -> gcp.cloudrunv2.Job:
    """
    Creates a Cloud Run Job that runs Alembic database migrations.

    A Cloud Run Job is a one-shot task — it runs to completion and exits.
    Exit code 0 = success. Non-zero = failure. No HTTP, no ports, no scaling.

    Why a Cloud Run Job instead of running migrations locally:
    - Cloud SQL's private IP (10.1.0.3) is only reachable from inside the VPC
    - The job runs inside the VPC via direct egress — no Auth Proxy needed
    - Migrations run in the same environment as the application
    - CI can trigger it with a single gcloud command: gcloud run jobs execute --wait
    - Failure stops the pipeline before any traffic shifts

    Same image as the service:
    - Guarantees migration code and app code are always at the same commit
    - No separate migration image to build, push, or keep in sync
    - The Dockerfile CMD (.venv/bin/uvicorn) is overridden here at job level

    Same SA as the service (cloudrun-sa):
    - Already has roles/cloudsql.client → can open connections to Cloud SQL
    - Already has secretAccessor on the database-url secret → reads the URL
    - No new SA needed — same identity, same database, same permissions

    max_retries=0:
    - Alembic is idempotent for fully-applied migrations (checks alembic_version)
    - But NOT safe to retry a partially-failed migration — fail fast instead
    - A failed migration should be investigated and fixed, not blindly retried

    timeout=600s (10 minutes):
    - Generous headroom for future schema changes (adding indexes to large tables)
    - Cloud Run Jobs default to 10 minutes anyway, but explicit is better

    Trigger manually:   make migrate
    Trigger in CI:      gcloud run jobs execute <job-name> --wait
    Downgrade:          make migrate-down (or REVISION=abc123 for specific target)
    """
    image = registry_url.apply(lambda url: f"{url}/backend:{IMAGE_TAG}")

    job = gcp.cloudrunv2.Job(
        "migrate-job",
        name=resource_name("migrate"),
        location=REGION,
        template=gcp.cloudrunv2.JobTemplateArgs(
            template=gcp.cloudrunv2.JobTemplateTemplateArgs(
                # cloudrun-sa is the identity this job runs as.
                # GCP attaches it automatically — no JSON key needed.
                service_account=sa.email,
                # Fail immediately on error — do not retry partial migrations.
                max_retries=0,
                # 10 minutes — enough for index creation on large tables.
                timeout="600s",
                containers=[
                    gcp.cloudrunv2.JobTemplateTemplateContainerArgs(
                        # Same image as the service, same git SHA.
                        image=image,
                        # Override the Dockerfile CMD.
                        # commands replaces the container ENTRYPOINT.
                        # args replaces the container CMD.
                        # Together they run: .venv/bin/alembic upgrade head
                        commands=[".venv/bin/alembic"],
                        args=["upgrade", "head"],
                        # DATABASE_URL from Secret Manager.
                        # Contains the private Cloud SQL IP (10.1.0.3) —
                        # reachable only from inside the VPC via egress below.
                        # cloudrun-sa already has secretAccessor on this secret.
                        envs=[
                            gcp.cloudrunv2.JobTemplateTemplateContainerEnvArgs(
                                name="DATABASE_URL",
                                value_source=gcp.cloudrunv2.JobTemplateTemplateContainerEnvValueSourceArgs(
                                    secret_key_ref=gcp.cloudrunv2.JobTemplateTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                        secret=secrets.database_url.secret_id,
                                        version="latest",
                                    ),
                                ),
                            ),
                        ],
                    )
                ],
                # Direct VPC Egress — identical config to the service.
                # Required so the job container can route to 10.1.0.3.
                # Without this, Cloud SQL's private IP is unreachable.
                #
                # PRIVATE_RANGES_ONLY: SQL traffic (10.x) routes through VPC.
                # Secret Manager calls go direct via private_ip_google_access
                # on the subnet — no VPC routing needed for Google APIs.
                vpc_access=gcp.cloudrunv2.JobTemplateTemplateVpcAccessArgs(
                    network_interfaces=[
                        gcp.cloudrunv2.JobTemplateTemplateVpcAccessNetworkInterfaceArgs(
                            network=vpc.name,
                            subnetwork=subnet.name,
                        )
                    ],
                    egress="PRIVATE_RANGES_ONLY",
                ),
            )
        ),
    )

    return job
