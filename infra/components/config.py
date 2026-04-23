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

# App name — read from Pulumi config so new projects can set their own prefix.
# Default defined in Pulumi.yaml: storyengine-infra:app: storyengine
# All GCP resource names derive from this via PREFIX and resource_name().
APP = _app.require("app")
PREFIX = f"{APP}-{STACK}"  # "storyengine-main"

# ── App-level config ───────────────────────────────────────────────────────────

IMAGE_TAG = _app.require("image_tag")  # git SHA set by make deploy-backend
GOOGLE_OAUTH_CLIENT_ID = _app.require("google_oauth_client_id")

# ── Derived values ─────────────────────────────────────────────────────────────

# Domain is set explicitly per stack in Pulumi.<stack>.yaml.
# e.g. storyengine-infra:domain: app.dekatha.com
# This decouples the domain from the stack name — "main" stack serves
# "app.dekatha.com", a future "dev" stack can serve "dev.dekatha.com".
DOMAIN = _app.require("domain")
FRONTEND_URL = f"https://{DOMAIN}"

# API subdomain — served via the same load balancer as the frontend.
# Routes to the Cloud Run backend service via a Serverless NEG.
# Decoupling into a separate LB is possible but costs ~$36/month extra.
API_DOMAIN = _app.require("api_domain")

# Media bucket name suffix — set once on first deploy, then never change.
# GCS bucket names are globally unique and immutable; changing this suffix
# means recreating the bucket (destructive — all media uploads are lost).
# For a new project: choose a short random string (e.g. run `openssl rand -hex 2`).
# Set it in Pulumi.<stack>.yaml as: <project>:media_bucket_suffix: <value>
_MEDIA_BUCKET_SUFFIX = _app.require("media_bucket_suffix")
MEDIA_BUCKET_NAME = f"{PREFIX}-media-{_MEDIA_BUCKET_SUFFIX}"

# PostgreSQL database name created inside Cloud SQL.
# Defaults to APP so a new project gets a sensibly-named database without
# any config required. Override in Pulumi.<stack>.yaml as:
#   <project>:db_name: mydbname
DB_NAME = _app.get("db_name") or APP

# GitHub repository allowed to authenticate via Workload Identity Federation.
# SECURITY: this is the access-control gate. Only tokens from this repo can
# impersonate github-actions-sa. Set correctly before running pulumi up.
# Format: "owner/repo" e.g. "acme/myapp"
# Set in Pulumi.<stack>.yaml as: <project>:github_repo: owner/repo
GITHUB_REPO = _app.require("github_repo")


def resource_name(suffix: str) -> str:
    """Returns the canonical resource name for this stack.

    Examples (main stack, app=storyengine):
        resource_name("backend")  → "storyengine-main-backend"
        resource_name("postgres") → "storyengine-main-postgres"
    """
    return f"{PREFIX}-{suffix}"
