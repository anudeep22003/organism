"""
Artifact Registry Docker repository component.

Creates the GCP Artifact Registry repository that stores Docker images for the app.

Usage:
    registry = DockerRegistry("registry")
    # Access resources:
    registry.repository  # gcp.artifactregistry.Repository
    registry.url         # pulumi.Output[str]  — full registry URL prefix

Attributes exposed:
    repository (gcp.artifactregistry.Repository): the registry resource
    url (pulumi.Output[str]): full image URL prefix, e.g.
        "europe-west2-docker.pkg.dev/my-project/storyengine-main"

Design decisions:
    - Images are tagged with git SHA (not "latest") — every push is
      permanently tied to the exact source commit it was built from.
    - The registry URL is derived from REGION + PROJECT + repository_id
      so callers never hardcode these values.
    - repository_id=PREFIX ties the registry name to the app+stack prefix,
      matching all other GCP resource names in this stack.

Image URL pattern:
    {url}/backend:{git-sha}
    e.g. europe-west2-docker.pkg.dev/my-project/storyengine-main/backend:abc1234

To push an image:
    docker push $(pulumi stack output registry_url)/backend:$(git rev-parse --short HEAD)
    # Or use: make deploy-backend
"""

import pulumi
import pulumi_gcp as gcp

from components.config import APP, PREFIX, PROJECT, REGION


class DockerRegistry(pulumi.ComponentResource):
    """
    Artifact Registry repository for storing Docker images.

    Artifact Registry is GCP's managed container registry — it stores,
    versions, and serves Docker images. Each image push is immutable and
    addressable by its SHA digest, making deployments fully traceable.

    Child resources (all parented to this component):
        {name}-repository   gcp.artifactregistry.Repository

    Derived attributes (not GCP resources):
        url   pulumi.Output[str] — the full registry URL prefix
    """

    repository: gcp.artifactregistry.Repository
    url: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:DockerRegistry", name, {}, opts)

        self.repository = gcp.artifactregistry.Repository(
            f"{name}-repository",
            repository_id=PREFIX,
            format="DOCKER",
            location=REGION,
            description="StoryEngine dev Docker images",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # The full registry URL is what Docker uses as the image name prefix.
        # Constructed from config values — no hardcoding the project or location
        # string outside of this file.
        self.url = pulumi.Output.concat(
            REGION,
            "-docker.pkg.dev/",
            PROJECT,
            "/",
            self.repository.repository_id,
        )

        self.register_outputs(
            {
                "repository": self.repository,
                "url": self.url,
            }
        )
