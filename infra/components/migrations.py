"""
Cloud Run migration job component.

Creates a Cloud Run Job that runs Alembic database migrations.

Usage:
    migrations = MigrationJob(
        "migrations",
        sa=cloudrun_sa.account,
        secrets=secrets,
        registry_url=registry.url,
        vpc=network.vpc,
        subnet=network.subnet,
    )
    migrations.name  # pulumi.Output[str] — the Cloud Run Job name

Attributes exposed:
    name (pulumi.Output[str]): the Cloud Run Job resource name
                               used by: make migrate, CI pipeline

Design decisions:
    - A Cloud Run Job is a one-shot task — it runs to completion and exits.
      Exit code 0 = success. Non-zero = failure. No HTTP, no ports, no scaling.

    - Same image as the service, same git SHA:
        Guarantees migration code and app code are always at the same commit.
        No separate migration image to build, push, or keep in sync.
        The Dockerfile CMD (.venv/bin/uvicorn) is overridden at job level.

    - Same SA as the service (cloudrun-sa):
        Already has roles/cloudsql.client → can open connections to Cloud SQL.
        Already has secretAccessor on the database-url secret → reads the URL.
        No new SA needed — same identity, same database, same permissions.

    - max_retries=0:
        Alembic is idempotent for fully-applied migrations (checks alembic_version)
        but NOT safe to retry a partially-failed migration — fail fast instead.
        A failed migration should be investigated and fixed, not blindly retried.

    - timeout (default "600s" / 10 minutes):
        Generous headroom for future schema changes (e.g. adding indexes to large
        tables). Cloud Run Jobs default to 10 minutes anyway, explicit is better.
        Override if your migrations routinely take longer (e.g. backfilling large tables).

    - Direct VPC Egress: Cloud SQL has a private IP (10.1.x.x) only reachable
      from inside the VPC. The job needs VPC egress to reach it.
      PRIVATE_RANGES_ONLY: SQL traffic routes through VPC; Secret Manager calls
      go direct via private_ip_google_access on the subnet.

Trigger manually:   make migrate
Trigger in CI:      gcloud run jobs execute <job-name> --wait
Check status:       gcloud run jobs executions list --job <job-name>
"""

import pulumi
import pulumi_gcp as gcp

from components.config import APP, IMAGE_TAG, REGION, resource_name
from components.secrets import AppSecrets


class MigrationJob(pulumi.ComponentResource):
    """
    Cloud Run Job for running Alembic database migrations.

    Runs alembic upgrade head inside the VPC using the same image as the
    Cloud Run service. Triggered manually or by the CI pipeline.

    Child resources (all parented to this component):
        {name}-job   gcp.cloudrunv2.Job
    """

    name: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        sa: gcp.serviceaccount.Account,
        secrets: AppSecrets,
        registry_url: pulumi.Output[str],
        vpc: gcp.compute.Network,
        subnet: gcp.compute.Subnetwork,
        timeout: str = "600s",
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:MigrationJob", name, {}, opts)

        image = registry_url.apply(lambda url: f"{url}/backend:{IMAGE_TAG}")

        job = gcp.cloudrunv2.Job(
            f"{name}-job",
            name=resource_name("migrate"),
            location=REGION,
            template=gcp.cloudrunv2.JobTemplateArgs(
                template=gcp.cloudrunv2.JobTemplateTemplateArgs(
                    # cloudrun-sa is the identity this job runs as.
                    # GCP attaches it automatically — no JSON key needed.
                    service_account=sa.email,
                    # Fail immediately on error — do not retry partial migrations.
                    max_retries=0,
                    timeout=timeout,
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
                    # Required so the job container can route to Cloud SQL's
                    # private IP. Without this, Cloud SQL is unreachable.
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
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.name = job.name

        self.register_outputs({"name": self.name})
