STACK       := dev
PROJECT     := shared-apps-infrastructure
REGION      := europe-west2
REGISTRY    := $(REGION)-docker.pkg.dev/$(PROJECT)/storyengine-dev
IMAGE       := $(REGISTRY)/backend
BACKEND_DIR := $(shell git rev-parse --show-toplevel)/backend

# The git SHA of HEAD in the backend directory.
# Using the monorepo root SHA keeps image tags consistent across all
# components — one SHA per commit, no per-subdirectory confusion.
SHA := $(shell git rev-parse --short HEAD)

# ── Pulumi ────────────────────────────────────────────────────────────────────

.PHONY: preview
preview:
	PULUMI_CONFIG_PASSPHRASE="" pulumi preview --stack $(STACK)

.PHONY: up
up:
	PULUMI_CONFIG_PASSPHRASE="" pulumi up --stack $(STACK)

.PHONY: outputs
outputs:
	PULUMI_CONFIG_PASSPHRASE="" pulumi stack output --stack $(STACK)

# ── Docker ────────────────────────────────────────────────────────────────────

.PHONY: build
build:
	docker build --platform linux/amd64 \
		-t $(IMAGE):$(SHA) \
		$(BACKEND_DIR)

.PHONY: push
push:
	docker push $(IMAGE):$(SHA)

# ── Deploy ────────────────────────────────────────────────────────────────────

# build-and-deploy: build the image, push it, stamp the SHA into Pulumi config,
# then run pulumi up — all in one command. The SHA is always the current HEAD,
# so the running revision is always traceable to an exact commit.
.PHONY: deploy
deploy: build push
	PULUMI_CONFIG_PASSPHRASE="" pulumi config set image_tag $(SHA) --stack $(STACK)
	PULUMI_CONFIG_PASSPHRASE="" pulumi up --stack $(STACK)

# ── Secrets ───────────────────────────────────────────────────────────────────

.PHONY: populate-secrets
populate-secrets:
	bash scripts/populate-secrets.sh

# ── Database migrations ───────────────────────────────────────────────────────

# Runs Alembic migrations against the Cloud SQL dev instance via the
# Cloud SQL Auth Proxy. The proxy must be running in a separate terminal:
#
#   cloud-sql-proxy shared-apps-infrastructure:europe-west2:storyengine-dev-postgres --port 5433
#
# The proxy handles IAM authentication to Cloud SQL — your local gcloud
# credentials are used, no password needed for the proxy itself. The
# DATABASE_URL still uses the appuser password for Postgres authentication.
#
# Read DATABASE_URL from Secret Manager and rewrite the host to point at
# the Cloud SQL Auth Proxy running on localhost:5433.
# The proxy tunnels to Cloud SQL using your gcloud ADC — no password needed
# for the tunnel itself. The URL still carries the DB credentials for Postgres
# authentication, but the network path goes through the proxy.
#
# sed replaces everything between :// and the next @ with the proxy address.
# e.g. postgresql+psycopg://appuser:pass@10.1.0.3:5432/storyengine
#   -> postgresql+psycopg://appuser:pass@localhost:5433/storyengine
CLOUD_DB_URL = $(shell gcloud secrets versions access latest \
	--secret storyengine-dev-database-url \
	--project $(PROJECT) 2>/dev/null)
PROXY_DB_URL = $(shell echo "$(CLOUD_DB_URL)" | sed 's/@[^/]*\//@localhost:5433\//')

.PHONY: migrate
migrate:
	@echo "Running migrations via Cloud SQL Auth Proxy on localhost:5433"
	@echo "Make sure the proxy is running in another terminal:"
	@echo "  cloud-sql-proxy $(PROJECT):$(REGION):storyengine-dev-postgres --port 5433"
	@echo ""
	@test -n "$(CLOUD_DB_URL)" || (echo "ERROR: Could not read DATABASE_URL from Secret Manager. Has pulumi up been run?"; exit 1)
	cd $(BACKEND_DIR) && DATABASE_URL="$(PROXY_DB_URL)" .venv/bin/alembic upgrade head
