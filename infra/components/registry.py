import pulumi
import pulumi_gcp as gcp

from components.config import PREFIX, PROJECT, REGION


def create_docker_registry() -> tuple[
    gcp.artifactregistry.Repository, pulumi.Output[str]
]:
    """
    Creates an Artifact Registry repository for storing Docker images.

    Artifact Registry is GCP's managed container registry — it stores,
    versions, and serves Docker images. Each image push is immutable and
    addressable by its SHA digest, making deployments fully traceable.

    The registry URL follows the pattern:
      <location>-docker.pkg.dev/<project>/<repository-id>/<image>:<tag>

    Images are tagged with the git commit SHA at build time (not 'latest'),
    so every pushed image is permanently tied to the exact source it was
    built from.
    """
    repository = gcp.artifactregistry.Repository(
        "docker-registry",
        repository_id=PREFIX,
        format="DOCKER",
        location=REGION,
        description="StoryEngine dev Docker images",
    )

    # The full registry URL is what Docker uses as the image name prefix.
    # We export it so callers have a single source of truth — no hardcoding
    # the project or location string outside of this file.
    registry_url = pulumi.Output.concat(
        REGION,
        "-docker.pkg.dev/",
        PROJECT,
        "/",
        repository.repository_id,
    )

    return repository, registry_url
