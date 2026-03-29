import pulumi
import pulumi_gcp as gcp

from components.config import (
    DOMAIN,
    IMAGE_TAG,
    MEDIA_BUCKET_NAME,
    PROJECT,
    REGION,
    resource_name,
)
from components.secrets import AppSecrets


def create_cloudrun_service(
    sa: gcp.serviceaccount.Account,
    secrets: AppSecrets,
    registry_url: pulumi.Output[str],
    vpc: gcp.compute.Network,
    subnet: gcp.compute.Subnetwork,
) -> tuple[gcp.cloudrunv2.Service, pulumi.Output[str]]:
    """
    Creates the Cloud Run service that runs the StoryEngine backend.

    The service definition declares everything Cloud Run needs:
    - Which container image to run (referenced by git SHA tag)
    - Which identity to run as (cloudrun-sa)
    - What environment the container sees (plain vars + secret refs)
    - How to know when the container is healthy (startup probe)
    - Who can call it (allUsers via run.invoker = public internet)

    Image tag is read from Pulumi stack config (image_tag).
    Set it before pulumi up with:
      pulumi config set image_tag $(git rev-parse --short HEAD)

    Scaling is capped at 2 instances for dev — prevents surprise bills
    while still allowing some concurrency. Scale-to-zero is enabled
    (min_instance_count=0) so idle time costs nothing.
    """
    image = registry_url.apply(lambda url: f"{url}/backend:{IMAGE_TAG}")

    # Non-sensitive config injected directly as plain env vars.
    # These are not secrets — knowing the project ID or bucket name
    # gives no one access to anything. No reason to encrypt them.
    plain_env_vars = [
        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(name=k, value=v)
        for k, v in {
            "GCP_PROJECT_ID": PROJECT,
            "GCP_REGION": REGION,
            "GCP_STORAGE_BUCKET": MEDIA_BUCKET_NAME,
            # Comma-separated list of allowed CORS origins.
            # Read in main.py via os.getenv("CORS_ORIGINS").
            # Not a secret — knowing this domain grants no access to anything.
            "CORS_ORIGINS": f"https://{DOMAIN}",
        }.items()
    ]

    # Build the list of secret env var references.
    # Cloud Run fetches these from Secret Manager at container startup
    # and injects them as normal env vars. The app reads os.getenv()
    # as usual — it never knows they came from Secret Manager.
    secret_env_vars = [
        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
            name="ANTHROPIC_API_KEY",
            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                    secret=secrets.anthropic_api_key.secret_id,
                    version="latest",
                ),
            ),
        ),
        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
            name="OPENAI_API_KEY",
            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                    secret=secrets.openai_api_key.secret_id,
                    version="latest",
                ),
            ),
        ),
        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
            name="FAL_API_KEY",
            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                    secret=secrets.fal_api_key.secret_id,
                    version="latest",
                ),
            ),
        ),
        gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
            name="DATABASE_URL",
            value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                    secret=secrets.database_url.secret_id,
                    version="latest",
                ),
            ),
        ),
    ]

    service = gcp.cloudrunv2.Service(
        "backend",
        name=resource_name("backend"),
        location=REGION,
        # Service-level scaling: GCP populates these API fields automatically.
        # Declaring them explicitly keeps Pulumi state in sync and prevents
        # spurious diffs on every preview.
        scaling=gcp.cloudrunv2.ServiceScalingArgs(
            min_instance_count=0,
        ),
        template=gcp.cloudrunv2.ServiceTemplateArgs(
            # cloudrun-sa is the identity this container runs as.
            # GCP attaches it automatically — no JSON key needed.
            service_account=sa.email,
            containers=[
                gcp.cloudrunv2.ServiceTemplateContainerArgs(
                    image=image,
                    envs=plain_env_vars + secret_env_vars,
                    # 512MB default OOMs on startup — the Python runtime,
                    # grpcio, pillow, and sqlalchemy together exceed it.
                    # 1Gi gives comfortable headroom for dev.
                    resources=gcp.cloudrunv2.ServiceTemplateContainerResourcesArgs(
                        limits={"memory": "1Gi", "cpu": "1"},
                    ),
                    # Startup probe: Cloud Run calls GET /health before
                    # routing any traffic to this revision. If it fails
                    # failure_threshold times, the revision is marked
                    # failed and the previous revision stays live.
                    startup_probe=gcp.cloudrunv2.ServiceTemplateContainerStartupProbeArgs(
                        http_get=gcp.cloudrunv2.ServiceTemplateContainerStartupProbeHttpGetArgs(
                            path="/health",
                        ),
                        initial_delay_seconds=5,
                        period_seconds=10,
                        failure_threshold=3,
                        timeout_seconds=5,
                    ),
                )
            ],
            scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
                # Scale to zero when idle — no traffic = no cost.
                min_instance_count=0,
                # Cap at 2 for dev — prevents surprise bills.
                max_instance_count=2,
            ),
            # Direct VPC Egress: attaches Cloud Run containers directly to
            # our subnet, giving them a VPC IP. This allows them to reach
            # Cloud SQL's private IP (10.1.x.x) without a VPC connector.
            #
            # egress=PRIVATE_RANGES_ONLY: only traffic destined for private
            # IP ranges (RFC 1918: 10.x, 172.16.x, 192.168.x) is routed
            # through the VPC. Public internet traffic and Google API calls
            # go direct — more efficient than ALL_TRAFFIC, and Google APIs
            # are reachable via private_ip_google_access on the subnet.
            vpc_access=gcp.cloudrunv2.ServiceTemplateVpcAccessArgs(
                network_interfaces=[
                    gcp.cloudrunv2.ServiceTemplateVpcAccessNetworkInterfaceArgs(
                        network=vpc.name,
                        subnetwork=subnet.name,
                    )
                ],
                egress="PRIVATE_RANGES_ONLY",
            ),
        ),
    )

    # Make the service publicly accessible.
    # allUsers is a special GCP identifier meaning "anyone on the internet".
    # roles/run.invoker is the permission to call (invoke) the service.
    # Without this binding, every request returns 403.
    gcp.cloudrunv2.ServiceIamMember(
        "backend-public-access",
        name=service.name,
        location=service.location,
        role="roles/run.invoker",
        member="allUsers",
    )

    return service, service.uri
