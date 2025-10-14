import os

import pulumi
import pulumi_gcp as gcp
from dotenv import load_dotenv
from pulumi_gcp.cloudrun import (
    ServiceMetadataArgs,
    ServiceTemplateArgs,
    ServiceTemplateMetadataArgs,
    ServiceTemplateSpecArgs,
    ServiceTemplateSpecContainerArgs,
    ServiceTemplateSpecContainerEnvArgs,
    ServiceTemplateSpecContainerEnvValueFromArgs,
    ServiceTemplateSpecContainerEnvValueFromSecretKeyRefArgs,
    ServiceTemplateSpecContainerPortArgs,
    ServiceTemplateSpecContainerResourcesArgs,
)

load_dotenv(override=True, dotenv_path="../.env.prod")

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "not even initialized")
github_token = os.getenv("GITHUB_TOKEN", "not even initialized")
# Read from Pulumi config instead of environment
image_tag = pulumi.Config().get("image_tag") or "latest"

infra_stack = pulumi.StackReference("anudeep22003-org/shared-apps-infra/prod")

# Get shared resources from the infra stack
vpc_connector_name = infra_stack.get_output("vpc_connector_name")
vpc_connector: pulumi.Output[gcp.vpcaccess.Connector] = infra_stack.get_output(
    "vpc_connector"
)
artifact_registry_url = infra_stack.get_output("artifact_registry_url")
project_id = infra_stack.get_output("project_id")
region = infra_stack.get_output("region")
enabled_apis: pulumi.Output[list[gcp.projects.Service]] = infra_stack.get_output(
    "enabled_apis"
)

# Pod-specific configuration
POD_NAME = "github-understand"

anthropic_secret = gcp.secretmanager.Secret(
    "anthropic-api-key",
    secret_id="anthropic-api-key",
    replication={"user_managed": {"replicas": [{"location": "us-central1"}]}},
)

anthropic_secret_version = gcp.secretmanager.SecretVersion(
    "anthropic-api-key-version",
    secret=anthropic_secret.id,
    secret_data=anthropic_api_key,  # Replace with actual API key
    opts=pulumi.ResourceOptions(depends_on=anthropic_secret),
)

github_secret = gcp.secretmanager.Secret(
    "github-token",
    secret_id="github-token",
    replication={"user_managed": {"replicas": [{"location": "us-central1"}]}},
)

github_secret_version = gcp.secretmanager.SecretVersion(
    "github-token-version",
    secret=github_secret.id,
    secret_data=github_token,
    opts=pulumi.ResourceOptions(depends_on=github_secret),
)


def create_pod(
    name: str,
    vpc_connector: pulumi.Output[gcp.vpcaccess.Connector],  # Change this type
    artifact_registry_url: pulumi.Output[str],
    anthropic_secret: gcp.secretmanager.Secret,
    github_secret: gcp.secretmanager.Secret,
    enabled_apis: pulumi.Output[list[gcp.projects.Service]],
    image_tag: str,
) -> dict:
    """Create a complete pod with service account, bucket, and Cloud Run service."""

    # 1. Service Account for this pod
    service_account = gcp.serviceaccount.Account(
        f"{name}-sa",
        account_id=f"{name}-service",
        display_name=f"{name.title()} Service Account",
    )

    # 2. Storage bucket for this pod
    bucket = gcp.storage.Bucket(
        f"{name}-bucket",
        name=f"{name}-{pulumi.get_project()}-{pulumi.get_stack()}",
        location="US-CENTRAL1",
        uniform_bucket_level_access=True,
        versioning={"enabled": True},
    )

    # 3. IAM: Service account access to its bucket
    gcp.storage.BucketIAMBinding(
        f"{name}-bucket-access",
        bucket=bucket.name,
        role="roles/storage.objectAdmin",
        members=[pulumi.Output.concat("serviceAccount:", service_account.email)],
        opts=pulumi.ResourceOptions(depends_on=service_account),
    )

    # 4. IAM: Service account access to secrets

    gcp.secretmanager.SecretIamMember(
        f"{name}-anthropic-secret-access",
        secret_id=anthropic_secret.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", service_account.email),
        opts=pulumi.ResourceOptions(depends_on=service_account),
    )

    gcp.secretmanager.SecretIamMember(
        f"{name}-github-secret-access",
        secret_id=github_secret.secret_id,
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", service_account.email),
        opts=pulumi.ResourceOptions(depends_on=service_account),
    )

    # 5. Cloud Run service
    service = gcp.cloudrun.Service(
        f"{name}-service",
        location="us-central1",
        metadata=ServiceMetadataArgs(
            annotations={
                "run.googleapis.com/ingress": "all",
            }
        ),
        template=ServiceTemplateArgs(
            metadata=ServiceTemplateMetadataArgs(
                annotations={
                    "run.googleapis.com/vpc-access-connector": vpc_connector_name,
                    "run.googleapis.com/vpc-access-egress": "all",
                }
            ),
            spec=ServiceTemplateSpecArgs(
                service_account_name=service_account.email,
                container_concurrency=100,
                timeout_seconds=900,  # 15 minutes for long-running Claude Code processes
                containers=[
                    ServiceTemplateSpecContainerArgs(
                        image=pulumi.Output.concat(
                            artifact_registry_url, f"/{name}:{image_tag}"
                        ),
                        ports=[
                            ServiceTemplateSpecContainerPortArgs(container_port=8000)
                        ],
                        resources=ServiceTemplateSpecContainerResourcesArgs(
                            limits={
                                "cpu": "2000m",
                                "memory": "2Gi",
                            }  # More resources for git/claude operations
                        ),
                        envs=[
                            ServiceTemplateSpecContainerEnvArgs(
                                name="BUCKET_NAME", value=bucket.name
                            ),
                            ServiceTemplateSpecContainerEnvArgs(
                                name="GOOGLE_CLOUD_PROJECT", value=pulumi.get_project()
                            ),
                            ServiceTemplateSpecContainerEnvArgs(
                                name="POD_NAME", value=name
                            ),
                            # Secrets will be mounted as env vars in production
                            ServiceTemplateSpecContainerEnvArgs(
                                name="GITHUB_TOKEN",
                                value_from=ServiceTemplateSpecContainerEnvValueFromArgs(
                                    secret_key_ref=ServiceTemplateSpecContainerEnvValueFromSecretKeyRefArgs(
                                        name=github_secret.secret_id,
                                        key="latest",
                                    )
                                ),
                            ),
                            ServiceTemplateSpecContainerEnvArgs(
                                name="ANTHROPIC_API_KEY",
                                value_from=ServiceTemplateSpecContainerEnvValueFromArgs(
                                    secret_key_ref=ServiceTemplateSpecContainerEnvValueFromSecretKeyRefArgs(
                                        name=anthropic_secret.secret_id,
                                        key="latest",
                                    )
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        opts=pulumi.ResourceOptions(
            depends_on=[service_account]
        ),  # Only use direct resources
    )

    # 6. Make the service publicly accessible
    gcp.cloudrun.IamBinding(
        f"{name}-public-access",
        location=service.location,
        service=service.name,
        role="roles/run.invoker",
        members=["allUsers"],  # Public access - restrict in production!
        opts=pulumi.ResourceOptions(depends_on=service),
    )

    return {
        "service_account": service_account,
        "bucket": bucket,
        "service": service,
        "url": service.statuses[0].url,
    }


output = create_pod(
    name=POD_NAME,
    vpc_connector=vpc_connector,
    artifact_registry_url=artifact_registry_url,
    anthropic_secret=anthropic_secret,
    github_secret=github_secret,
    enabled_apis=enabled_apis,
    image_tag=image_tag,
)

pulumi.export("pod", output)
