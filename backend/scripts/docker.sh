#!/bin/bash

set -e

IMAGE_NAME="github-understand"
HOST_PORT="8134"
DOCKER_PORT="8000"
STACK="dev"

# Generate image tag - use provided tag or generate timestamp-based tag
if [ -n "$IMAGE_TAG" ]; then
    TAG="$IMAGE_TAG"
else
    TAG=$(date +%Y%m%d-%H%M%S)
fi

# Get artifact registry URL from Pulumi (run from infra directory)
echo "Getting artifact registry URL from Pulumi..."
cd ~/@anudeep/infra/shared-apps-infra
ARTIFACT_REGISTRY_URL=$(pulumi stack output artifact_registry_url)

cd ~/@anudeep/projects/Sidebrain/github-repo-understand/backend

if [ -z "$ARTIFACT_REGISTRY_URL" ]; then
    echo "Error: Could not get artifact registry URL from Pulumi"
    exit 1
fi

FULL_IMAGE_NAME="${ARTIFACT_REGISTRY_URL}/${IMAGE_NAME}:${TAG}"

echo "Building image ${FULL_IMAGE_NAME}"
docker build --platform linux/amd64 -t ${IMAGE_NAME} -t ${FULL_IMAGE_NAME} .
echo "Image built"

echo "Pushing image to artifact registry..."
docker push ${FULL_IMAGE_NAME}
echo "Image pushed to ${FULL_IMAGE_NAME}"

# Export the tag for use in Pulumi deployment
export IMAGE_TAG=${TAG}
echo "Image tag exported: ${TAG}"

# Optional: Run locally for testing
if [ "$1" = "--run-local" ]; then
    echo "Running container ${IMAGE_NAME} on port ${HOST_PORT}"
    docker run -p ${HOST_PORT}:${DOCKER_PORT} ${IMAGE_NAME}
    echo "Container running"
    
    echo "Checking if server is running"
    curl http://localhost:${HOST_PORT}
    echo "Server is running"
fi

cd infra
echo "Setting image tag in Pulumi config for ${STACK} stack"
pulumi config set image_tag ${TAG} --stack ${STACK}
echo "Tag ${TAG} set in Pulumi config for ${STACK} stack"
cd -
