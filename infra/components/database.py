import pulumi
import pulumi_gcp as gcp
import pulumi_random as random

from components.config import REGION, resource_name
from components.secrets import AppSecrets

_DB_VERSION = "POSTGRES_16"
_DB_NAME = "storyengine"
_DB_USER = "appuser"


class DatabaseOutputs:
    """
    Holds references to all database resources and the constructed
    DATABASE_URL. Passed to __main__.py so it can write the URL to
    Secret Manager and export outputs.
    """

    def __init__(
        self,
        instance: gcp.sql.DatabaseInstance,
        database: gcp.sql.Database,
        user: gcp.sql.User,
        database_url: pulumi.Output[str],
    ) -> None:
        self.instance = instance
        self.database = database
        self.user = user
        self.database_url = database_url


def create_database(
    vpc: gcp.compute.Network,
    peering_connection: gcp.servicenetworking.Connection,
    secrets: AppSecrets,
) -> DatabaseOutputs:
    """
    Creates a Cloud SQL Postgres 16 instance with private IP only,
    the application database, and the application user.

    Password management: the DB password is generated randomly by Pulumi
    on first run and stored in Secret Manager. It is never stored in
    Pulumi config or git. To retrieve it:

      gcloud secrets versions access latest \\
        --secret <stack-prefix>-db-password \\
        --project <project>

    The make migrate target reads it automatically from Secret Manager.

    Private IP only (ipv4_enabled=False): the instance has no public
    endpoint. The only ways to reach it are:
      1. From within the VPC (Cloud Run via direct egress)
      2. Via the Cloud SQL Auth Proxy (uses IAM auth for the tunnel,
         then app credentials for Postgres auth)

    deletion_protection=False: allows pulumi destroy in dev. Set True in prod.
    ZONAL availability: single zone, no failover. Half the cost of REGIONAL.
    backup_configuration enabled=False: no automated backups for dev.
    """
    # Generate a random password for the database user.
    # special=False avoids characters that need URL-encoding in connection strings.
    # Pulumi stores this in its state (encrypted) and only changes it if the
    # resource is replaced. The value is also written to Secret Manager below
    # so it's always retrievable independently of Pulumi state.
    db_password = random.RandomPassword(
        "db-password",
        length=32,
        special=False,
    )

    # Store the generated password in Secret Manager immediately.
    # This is the single source of truth for the password — Pulumi state
    # has it too, but Secret Manager is where operators retrieve it.
    gcp.secretmanager.SecretVersion(
        "db-password-version",
        secret=secrets.db_password.id,
        secret_data=db_password.result,
    )

    # Grant cloudrun-sa access to read the db_password secret.
    # Not strictly needed at runtime (Cloud Run reads DATABASE_URL, not the
    # raw password) but useful for debugging and future tooling.
    # We skip this for now — cloudrun-sa only needs DATABASE_URL.

    instance = gcp.sql.DatabaseInstance(
        "postgres",
        name=resource_name("postgres"),
        database_version=_DB_VERSION,
        region=REGION,
        deletion_protection=False,
        # Explicit dependency: peering must be fully established before Cloud
        # SQL is created. Without this Pulumi runs them in parallel and Cloud
        # SQL fails with "network doesn't have at least 1 private services
        # connection". Pulumi can't infer this dependency automatically because
        # the connection resource isn't referenced in the instance's arguments.
        opts=pulumi.ResourceOptions(depends_on=[peering_connection]),
        settings=gcp.sql.DatabaseInstanceSettingsArgs(
            tier="db-f1-micro",
            # Explicitly set ENTERPRISE edition. GCP now defaults to
            # ENTERPRISE_PLUS which requires the db-perf-optimized-N-*
            # tier family. ENTERPRISE supports db-f1-micro, which is
            # the cheapest option (~$7/month) and sufficient for dev.
            edition="ENTERPRISE",
            availability_type="ZONAL",
            disk_autoresize=True,
            disk_size=10,
            disk_type="PD_SSD",
            ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
                # Public IP enabled so the Cloud SQL Auth Proxy can connect
                # from developer laptops for local migrations. The public IP
                # is not accessible directly — no authorized networks are
                # configured, so all direct connections are rejected. Only
                # the Auth Proxy (which uses IAM auth via TLS tunnel) can use
                # this path. Cloud Run uses the private IP via VPC egress.
                ipv4_enabled=True,
                private_network=vpc.id,
                # Allows Cloud SQL to be reached by Google-internal services
                # via direct VPC egress without a public IP.
                enable_private_path_for_google_cloud_services=True,
            ),
            backup_configuration=gcp.sql.DatabaseInstanceSettingsBackupConfigurationArgs(
                enabled=False,
            ),
        ),
    )

    database = gcp.sql.Database(
        "appdb",
        name=_DB_NAME,
        instance=instance.name,
    )

    user = gcp.sql.User(
        "appuser",
        name=_DB_USER,
        instance=instance.name,
        password=db_password.result,
    )

    # Construct the full DATABASE_URL from the private IP (known only after
    # Cloud SQL is created) and the generated password.
    # pulumi.Output.all() waits for both outputs to resolve before applying.
    database_url = pulumi.Output.all(
        instance.private_ip_address, db_password.result
    ).apply(
        lambda args: f"postgresql+psycopg://{_DB_USER}:{args[1]}@{args[0]}:5432/{_DB_NAME}"
    )

    return DatabaseOutputs(
        instance=instance,
        database=database,
        user=user,
        database_url=database_url,
    )
