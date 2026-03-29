STACK           := dev
PROJECT         := $(shell pulumi config get gcp:project --stack $(STACK) 2>/dev/null)
REGION          := $(shell pulumi config get gcp:region --stack $(STACK) 2>/dev/null)
REGISTRY        := $(REGION)-docker.pkg.dev/$(PROJECT)/storyengine-$(STACK)
IMAGE           := $(REGISTRY)/backend
BACKEND_DIR     := $(shell git rev-parse --show-toplevel)/backend
FRONTEND_DIR    := $(shell git rev-parse --show-toplevel)/frontend
FRONTEND_BUCKET := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output frontend_bucket --stack $(STACK) 2>/dev/null)
DB_INSTANCE     := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output db_instance_name --stack $(STACK) 2>/dev/null)
MIGRATION_JOB   := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output migration_job_name --stack $(STACK) 2>/dev/null)
SA_KEY          := $(shell git rev-parse --show-toplevel)/infra/keys/$(STACK)-storage-sa-key.json

# Git SHA of HEAD — used as the Docker image tag so every deployed revision
# is traceable to an exact commit. Never use 'latest' as a tag in production.
SHA := $(shell git rev-parse --short HEAD)

# ── Help ──────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "StoryEngine Dev — available make targets"
	@echo ""
	@echo "  Setup"
	@echo "    make setup              One-time onboarding instructions"
	@echo ""
	@echo "  Deploy"
	@echo "    make deploy-backend     Build + push image + deploy backend to Cloud Run"
	@echo "    make deploy-frontend    Build frontend + sync to GCS bucket"
	@echo "    make deploy-all         Deploy both backend and frontend"
	@echo ""
	@echo "  Database"
	@echo "    make migrate            Run forward migrations via Cloud Run Job"
	@echo "    make migrate-down       Downgrade one step (REVISION=abc123 for specific)"
	@echo "    make migrate-status     Show current DB migration version (needs make proxy)"
	@echo "    make migrate-history    Show full migration history (needs make proxy)"
	@echo "    make proxy              Start Auth Proxy on :5433 (inspection only)"
	@echo ""
	@echo "  Secrets"
	@echo "    make populate-secrets   Push secrets from .env.local to Secret Manager"
	@echo "    make rotate-secrets     Rotate secrets + force Cloud Run redeploy"
	@echo ""
	@echo "  Infra"
	@echo "    make preview            Show what pulumi up would change (dry run)"
	@echo "    make up                 Apply infra changes only (no image rebuild)"
	@echo "    make status             Show cert, Cloud Run revision, and stack outputs"
	@echo "    make outputs            Show all Pulumi stack outputs"
	@echo ""

# ── Setup (one-time onboarding) ───────────────────────────────────────────────

# Run this once on a new machine or when onboarding a new developer.
# Each step is idempotent — safe to re-run if something was missed.
.PHONY: setup
setup:
	@echo ""
	@echo "=== StoryEngine dev environment setup ==="
	@echo ""
	@echo "Step 1 — Authenticate with GCP:"
	@echo "  gcloud auth login"
	@echo "  gcloud auth application-default login"
	@echo ""
	@echo "Step 2 — Authenticate Docker to Artifact Registry (one-time):"
	@echo "  gcloud auth configure-docker $(REGION)-docker.pkg.dev"
	@echo ""
	@echo "Step 3 — Install Cloud SQL Auth Proxy (for inspection commands):"
	@echo "  brew install cloud-sql-proxy"
	@echo ""
	@echo "Step 4 — Add Pulumi passphrase to your shell profile (~/.zshrc or ~/.bashrc):"
	@echo "  export PULUMI_CONFIG_PASSPHRASE=''"
	@echo ""
	@echo "Step 5 — Download the localhost service account key:"
	@echo "  gcloud iam service-accounts keys create $(SA_KEY) \\"
	@echo "    --iam-account=localhost-sa@$(PROJECT).iam.gserviceaccount.com"
	@echo ""
	@echo "Step 6 — Add to backend/.env.local:"
	@echo "  GOOGLE_APPLICATION_CREDENTIALS=$(SA_KEY)"
	@echo ""
	@echo "Step 7 — Populate secrets from backend/.env.local:"
	@echo "  make populate-secrets"
	@echo ""
	@echo "Step 8 — Run initial database migrations:"
	@echo "  make migrate    # triggers Cloud Run Job, no proxy needed"
	@echo ""

# ── Pulumi ────────────────────────────────────────────────────────────────────

# Dry run — shows exactly what pulumi up would create/update/delete.
# Always run this before make up when making non-trivial infra changes.
.PHONY: preview
preview:
	PULUMI_CONFIG_PASSPHRASE="" pulumi preview --stack $(STACK)

# Apply infra changes only — does NOT rebuild the Docker image.
# Use this when you've only changed Pulumi components (env vars, IAM, etc.)
# and don't need a new backend revision. Use make deploy-backend if you
# also have code changes.
.PHONY: up
up:
	PULUMI_CONFIG_PASSPHRASE="" pulumi up --stack $(STACK) --yes

# Show all stack outputs: URLs, bucket names, IPs, SA emails etc.
.PHONY: outputs
outputs:
	PULUMI_CONFIG_PASSPHRASE="" pulumi stack output --stack $(STACK)

# ── Status ────────────────────────────────────────────────────────────────────

# Single command to see the health of everything deployed.
# Useful after a deploy or when debugging connectivity issues.
.PHONY: status
status:
	@echo ""
	@echo "=== Cloud Run (backend) ==="
	@gcloud run services describe storyengine-$(STACK)-backend \
		--region $(REGION) --project $(PROJECT) \
		--format="table(status.latestReadyRevisionName, status.url)" 2>&1
	@echo ""
	@echo "=== Migration Job ==="
	@gcloud run jobs describe $(MIGRATION_JOB) \
		--region $(REGION) --project $(PROJECT) \
		--format="table(metadata.name, status.conditions[0].status)" 2>&1
	@echo ""
	@echo "=== SSL Certificate ==="
	@gcloud compute ssl-certificates describe storyengine-$(STACK)-frontend-cert \
		--global --project $(PROJECT) \
		--format="table(name, managed.status, managed.domainStatus)" 2>&1
	@echo ""
	@echo "=== DNS resolution ==="
	@dig $(STACK).dekatha.com A +short 2>&1
	@echo "(should be 136.110.212.53)"
	@echo ""
	@echo "=== Stack outputs ==="
	@PULUMI_CONFIG_PASSPHRASE="" pulumi stack output --stack $(STACK)

# ── Docker ────────────────────────────────────────────────────────────────────

.PHONY: build
build:
	docker build --platform linux/amd64 \
		-t $(IMAGE):$(SHA) \
		$(BACKEND_DIR)

.PHONY: push
push:
	docker push $(IMAGE):$(SHA)

# ── Backend deploy ────────────────────────────────────────────────────────────

# Full backend deploy: build image → push to Artifact Registry →
# stamp SHA into Pulumi config → run pulumi up to update Cloud Run + Job.
#
# The SHA tag means every running revision is traceable to the exact commit
# it was built from. Rollback = set image_tag to a previous SHA + make up.
#
# Gotcha: if you also rotated secrets, run make rotate-secrets instead —
# that chains populate-secrets before the deploy so Cloud Run picks up
# the new secret values in the same revision.
.PHONY: deploy-backend
deploy-backend: build push
	PULUMI_CONFIG_PASSPHRASE="" pulumi config set image_tag $(SHA) --stack $(STACK)
	PULUMI_CONFIG_PASSPHRASE="" pulumi up --stack $(STACK) --yes

# ── Frontend deploy ───────────────────────────────────────────────────────────

# Build the Vite/React app and sync the output to the GCS bucket.
#
# Vite loads .env.production at build time — VITE_BACKEND_URL and other
# vars are baked into the JS bundle. The bucket serves the built files
# directly; the load balancer at 136.110.212.53 handles SSL termination.
#
# --delete-unmatched-destination-objects removes stale files from previous
# builds. Critical because Vite uses content-hashed filenames (main.abc123.js)
# and old versions accumulate in the bucket without this flag, bloating
# storage and potentially serving outdated assets.
.PHONY: build-frontend
build-frontend:
	cd $(FRONTEND_DIR) && npm run build

.PHONY: sync-frontend
sync-frontend:
	gcloud storage rsync $(FRONTEND_DIR)/dist/ gs://$(FRONTEND_BUCKET) \
		--recursive \
		--delete-unmatched-destination-objects \
		--project $(PROJECT)

.PHONY: deploy-frontend
deploy-frontend: build-frontend sync-frontend
	@echo ""
	@echo "Frontend deployed to gs://$(FRONTEND_BUCKET)"
	@echo "Live at: https://$(FRONTEND_BUCKET)"

# ── Deploy both ───────────────────────────────────────────────────────────────

# Deploy backend and frontend together in one command.
# Use this when a feature touches both (e.g. new API endpoint + UI change).
# Backend deploys first so the new API is live before the new frontend
# starts calling it — avoids a window where the new UI calls an endpoint
# that doesn't exist yet.
.PHONY: deploy-all
deploy-all: deploy-backend deploy-frontend

# ── Secrets ───────────────────────────────────────────────────────────────────

# Push secrets from backend/.env.local to GCP Secret Manager.
# Only keys under the "# --- secrets ---" section are uploaded.
# Idempotent — only creates a new version if the value has changed.
#
# Run this when:
#   - Setting up a new environment for the first time
#   - Rotating an API key (update .env.local first, then run this)
#
# After rotating secrets, Cloud Run needs a new revision to pick them up
# (it caches secret values at container startup). Use make rotate-secrets
# instead of this target if you want the rotation + redeploy in one step.
.PHONY: populate-secrets
populate-secrets:
	bash scripts/populate-secrets.sh

# Rotate secrets AND force a Cloud Run redeploy so the new values take effect.
#
# Why the redeploy is necessary: Cloud Run fetches secret values at container
# startup and caches them for the lifetime of the instance. If you only run
# populate-secrets, existing instances keep the old values until they restart.
# deploy-backend forces a new revision which pulls the latest secret versions.
.PHONY: rotate-secrets
rotate-secrets: populate-secrets deploy-backend
	@echo ""
	@echo "Secrets rotated and Cloud Run redeployed with latest values."

# ── Database migrations ───────────────────────────────────────────────────────

# Used by migrate-status and migrate-history (inspection commands via proxy).
# Standard forward migrations use the Cloud Run Job and don't need these.
CLOUD_DB_URL = $(shell gcloud secrets versions access latest \
	--secret $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output secret_database_url --stack $(STACK) 2>/dev/null) \
	--project $(PROJECT) 2>/dev/null)
PROXY_DB_URL = $(shell echo "$(CLOUD_DB_URL)" | sed 's/@[^/]*\//@localhost:5433\//')

# Run forward migrations via Cloud Run Job.
#
# The job runs inside the VPC (storyengine-dev-subnet) and reaches Cloud SQL
# at 10.1.0.3 directly — no Auth Proxy needed. Uses the same image as the
# service (same git SHA) so migration code and app code are always in sync.
#
# Blocks until the job completes. Exit code mirrors the job's exit code —
# a failed migration will exit non-zero and stop any calling script (e.g. CI).
#
# This is the standard migration path for both local dev and the CI/CD pipeline.
.PHONY: migrate
migrate:
	@echo "Running migrations via Cloud Run Job..."
	gcloud run jobs execute $(MIGRATION_JOB) \
		--region $(REGION) \
		--project $(PROJECT) \
		--wait
	@echo ""
	@echo "Migrations complete."

# Downgrade one migration step — manual recovery operation only.
# Never called from CI. To target a specific revision:
#   make migrate-down REVISION=abc123def456
# Default: one step back (-1).
#
# Recovery sequence after a bad migration:
#   1. make migrate-down            (schema rolls back)
#   2. pulumi config set image_tag  (point to previous good SHA)
#   3. make up                      (Cloud Run rolls back to old image)
.PHONY: migrate-down
migrate-down:
	@echo "Running downgrade via Cloud Run Job..."
	gcloud run jobs execute $(MIGRATION_JOB) \
		--region $(REGION) \
		--project $(PROJECT) \
		--args="downgrade,$(or $(REVISION),-1)" \
		--wait
	@echo ""
	@echo "Downgrade complete."

# Show the current migration version applied to the database.
# Requires the Auth Proxy to be running: make proxy
.PHONY: migrate-status
migrate-status:
	@lsof -i :5433 > /dev/null 2>&1 || \
		(echo "ERROR: Proxy not running. Run 'make proxy' first."; exit 1)
	cd $(BACKEND_DIR) && DATABASE_URL="$(PROXY_DB_URL)" .venv/bin/alembic current

# Show full migration history — applied and pending.
# Requires the Auth Proxy to be running: make proxy
.PHONY: migrate-history
migrate-history:
	@lsof -i :5433 > /dev/null 2>&1 || \
		(echo "ERROR: Proxy not running. Run 'make proxy' first."; exit 1)
	cd $(BACKEND_DIR) && DATABASE_URL="$(PROXY_DB_URL)" .venv/bin/alembic history --verbose

# Start the Cloud SQL Auth Proxy on localhost:5433.
#
# Standard migrations now use 'make migrate' (Cloud Run Job — no proxy needed).
# The proxy is only needed for inspection commands:
#   make migrate-status   (query current alembic version)
#   make migrate-history  (view full migration history)
#   manual psql, alembic downgrade, alembic stamp, etc.
#
# The proxy uses your local gcloud ADC credentials to create an
# IAM-authenticated TLS tunnel to Cloud SQL. Cloud SQL has a public IP
# enabled but NO authorized networks — the proxy is the only external path in.
#
# To stop the proxy: kill $(lsof -ti :5433)
.PHONY: proxy
proxy:
	@echo "Starting Cloud SQL Auth Proxy on localhost:5433..."
	@cloud-sql-proxy $(PROJECT):$(REGION):$(DB_INSTANCE) --port 5433 &
	@echo "Proxy PID: $$!"
	@echo "To stop: kill \$$(lsof -ti :5433)"
	@sleep 2
	@echo "Proxy ready."
