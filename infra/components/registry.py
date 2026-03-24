import pulumi
import pulumi_gcp as gcp

REGISTRY_ID = "storyengine-dev"
LOCATION = "europe-west2"


def create_docker_registry() -> gcp.artifactregistry.Repository:
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
    project = pulumi.Config("gcp").require("project")

    repository = gcp.artifactregistry.Repository(
        "docker-registry",
        repository_id=REGISTRY_ID,
        format="DOCKER",
        location=LOCATION,
        description="StoryEngine dev Docker images",
    )

    # The full registry URL is what Docker uses as the image name prefix.
    # We export it so callers have a single source of truth — no hardcoding
    # the project or location string outside of this file.
    registry_url = pulumi.Output.concat(
        LOCATION,
        "-docker.pkg.dev/",
        project,
        "/",
        repository.repository_id,
    )

    return repository, registry_url
