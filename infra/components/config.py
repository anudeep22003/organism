"""
Central configuration for the StoryEngine infrastructure.

All environment-specific values are derived from here.
To change region, project, or stack-level settings, edit Pulumi.dev.yaml
(or the relevant Pulumi.<stack>.yaml) — never hardcode these values in
individual component files.

Usage in components:
    from components.config import PROJECT, REGION, PREFIX, IMAGE_TAG, resource_name
"""

import pulumi

_gcp = pulumi.Config("gcp")
_app = pulumi.Config()

# ── GCP identity ───────────────────────────────────────────────────────────────

PROJECT = _gcp.require("project")  # e.g. "shared-apps-infrastructure"
REGION = _gcp.require("region")  # e.g. "europe-west2"

# ── Stack / naming ─────────────────────────────────────────────────────────────

STACK = pulumi.get_stack()  # "dev", "staging", "prod" — active stack name
APP = "storyengine"
PREFIX = f"{APP}-{STACK}"  # "storyengine-dev"

# ── App-level config ───────────────────────────────────────────────────────────

IMAGE_TAG = _app.require("image_tag")  # git SHA set by make deploy-backend

# ── Derived values ─────────────────────────────────────────────────────────────

# Domain is set explicitly per stack in Pulumi.<stack>.yaml.
# e.g. storyengine-infra:domain: app.dekatha.com
# This decouples the domain from the stack name — "main" stack serves
# "app.dekatha.com", a future "dev" stack can serve "dev.dekatha.com".
DOMAIN = _app.require("domain")

# API subdomain — served via the same load balancer as the frontend.
# Routes to the Cloud Run backend service via a Serverless NEG.
# Decoupling into a separate LB is possible but costs ~$36/month extra.
API_DOMAIN = _app.require("api_domain")

# Media bucket name. The x7k2 suffix was generated on first creation to
# avoid naming conflicts. It is intentionally static — GCS bucket names are
# globally unique and immutable. Change this only if you intend to recreate
# the bucket (which is destructive).
MEDIA_BUCKET_NAME = f"{PREFIX}-media-x7k2"


def resource_name(suffix: str) -> str:
    """Returns the canonical resource name for this stack.

    Examples (dev stack):
        resource_name("backend")  → "storyengine-dev-backend"
        resource_name("postgres") → "storyengine-dev-postgres"
    """
    return f"{PREFIX}-{suffix}"
