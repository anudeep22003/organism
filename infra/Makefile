STACK           := main
PROJECT         := $(shell pulumi config get gcp:project --stack $(STACK) 2>/dev/null)
REGION          := $(shell pulumi config get gcp:region --stack $(STACK) 2>/dev/null)
# PULUMI_PROJECT reads the project name directly from Pulumi.yaml.
# This drives the config key namespace (e.g. storyengine-infra:app).
# For a new project, changing name: in Pulumi.yaml is the only change needed here.
PULUMI_PROJECT  := $(shell grep "^name:" Pulumi.yaml | awk '{print $$2}')
# APP and PREFIX drive all GCP resource names — must match config.py.
# Reads from Pulumi config using the project name as the namespace prefix.
APP             := $(shell pulumi config get $(PULUMI_PROJECT):app --stack $(STACK) 2>/dev/null)
PREFIX          := $(APP)-$(STACK)
# REGISTRY reads from stack output — derived from PROJECT + APP + STACK in registry.py.
# Never construct this manually; the stack output is the single source of truth.
REGISTRY        := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output registry_url --stack $(STACK) 2>/dev/null)
IMAGE           := $(REGISTRY)/backend
BACKEND_DIR     := $(shell git rev-parse --show-toplevel)/backend
FRONTEND_DIR    := $(shell git rev-parse --show-toplevel)/frontend
FRONTEND_BUCKET := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output frontend_bucket --stack $(STACK) 2>/dev/null)
FRONTEND_URL    := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output frontend_url --stack $(STACK) 2>/dev/null)
SERVICE_URL     := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output api_url --stack $(STACK) 2>/dev/null)
DB_INSTANCE     := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output db_instance_name --stack $(STACK) 2>/dev/null)
MIGRATION_JOB   := $(shell PULUMI_CONFIG_PASSPHRASE="" pulumi stack output migration_job_name --stack $(STACK) 2>/dev/null)
SA_KEY          := $(shell git rev-parse --show-toplevel)/infra/keys/$(STACK)-localhost-sa-key.json

# Git SHA of HEAD — used as the Docker image tag so every deployed revision
# is traceable to an exact commit. Never use 'latest' as a tag in production.
SHA := $(shell git rev-parse --short HEAD)

# ── Help ──────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "StoryEngine Dev — available make targets"
	@echo ""
	@echo "  New project"
	@echo "    make init-project       Generate Pulumi.<stack>.yaml template for a new project"
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
	@echo "    make destroy            Tear down all infrastructure for this stack"
	@echo "    make status             Show cert, Cloud Run revision, and stack outputs"
	@echo "    make outputs            Show all Pulumi stack outputs"
	@echo "    make change-domain      Step-by-step instructions for switching domains"
	@echo ""

# ── New project bootstrap ─────────────────────────────────────────────────────

# Generates Pulumi.$(STACK).yaml with the correct config key prefix and an
# auto-generated media_bucket_suffix. Run this once after cloning this repo
# for a new project.
#
# Prerequisites (do these FIRST, before running this target):
#   1. Edit Pulumi.yaml:
#        - Change `name:` to your project name (e.g. myapp-infra)
#        - Change `storyengine-infra:app:` key to `myapp-infra:app: myapp`
#      The project name drives the config key namespace — it must match before
#      this target runs so the generated file has the correct prefix.
#
# After running this target:
#   2. Fill in every <...> placeholder in the generated Pulumi.$(STACK).yaml
#   3. pulumi stack init $(STACK)
#   4. make up
#   5. make setup    (developer onboarding instructions)
.PHONY: init-project
init-project:
	@if [ -f Pulumi.$(STACK).yaml ]; then \
		echo ""; \
		echo "ERROR: Pulumi.$(STACK).yaml already exists."; \
		echo "Delete it first if you want to regenerate it."; \
		echo ""; \
		exit 1; \
	fi
	@SUFFIX=$$(openssl rand -hex 2); \
	printf '%s\n' \
		'# Generated by make init-project — fill in every <...> value before running make up.' \
		'#' \
		'# Key prefix ("$(PULUMI_PROJECT):") matches the `name:` field in Pulumi.yaml.' \
		'# If you have not renamed Pulumi.yaml yet, do that first — then re-run make init-project.' \
		'#' \
		'# Steps after filling this in:' \
		'#   pulumi stack init $(STACK)' \
		'#   make up' \
		'#   make setup' \
		'config:' \
		'  gcp:project: <your-gcp-project-id>           # e.g. my-gcp-project-123' \
		'  gcp:region: <your-region>                     # e.g. europe-west2' \
		'  $(PULUMI_PROJECT):app: <your-app-name>        # lowercase, no spaces — drives all GCP resource names' \
		'  $(PULUMI_PROJECT):domain: <app.yourdomain.com>' \
		'  $(PULUMI_PROJECT):api_domain: <api.yourdomain.com>' \
		'  $(PULUMI_PROJECT):github_repo: <owner/repo>   # SECURITY: only this repo authenticates via WIF' \
		"  $(PULUMI_PROJECT):media_bucket_suffix: $$SUFFIX  # auto-generated — set once, NEVER change after first deploy" \
		'  $(PULUMI_PROJECT):image_tag: latest            # updated automatically by make deploy-backend' \
		> Pulumi.$(STACK).yaml
	@echo ""
	@echo "Generated Pulumi.$(STACK).yaml"
	@echo ""
	@echo "Next: fill in every <...> placeholder, then:"
	@echo "  pulumi stack init $(STACK)"
	@echo "  make up"
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
	@echo "Step 9 — Set GitHub Actions repository variables (one-time, per repo):"
	@echo "  Go to: GitHub repo → Settings → Secrets and variables → Actions → Variables"
	@echo "  Add the following variable (not secret — it is not sensitive):"
	@echo ""
	@echo "    PULUMI_BACKEND_URL = gs://my-app-pulumi-state"
	@echo ""
	@echo "  Why: Pulumi defaults to Pulumi Cloud in non-interactive sessions."
	@echo "  This variable tells the CI pipeline to use the GCS state backend instead."
	@echo "  It cannot be read from Pulumi itself — it is the bootstrap value that"
	@echo "  Pulumi needs before it can run any command."
	@echo ""
	@echo "  Also add the two Workload Identity secrets (from pulumi stack output):"
	@echo "    GCP_WORKLOAD_IDENTITY_PROVIDER = \$$(pulumi stack output workload_identity_provider --stack main)"
	@echo "    GCP_SERVICE_ACCOUNT            = \$$(pulumi stack output github_actions_sa_email --stack main)"
	@echo ""

# ── Domain change (checklist) ─────────────────────────────────────────────────

# Prints the exact steps to switch the stack to a new domain.
# Not a fully automated target — a DNS change at the registrar is required
# in the middle, which cannot be scripted. Follow each step in order.
.PHONY: change-domain
change-domain:
	@echo ""
	@echo "=== Domain change checklist ==="
	@echo ""
	@echo "Current domains:"
	@echo "  frontend : $$(PULUMI_CONFIG_PASSPHRASE="" pulumi config get $(PULUMI_PROJECT):domain --stack $(STACK) 2>/dev/null)"
	@echo "  api      : $$(PULUMI_CONFIG_PASSPHRASE="" pulumi config get $(PULUMI_PROJECT):api_domain --stack $(STACK) 2>/dev/null)"
	@echo ""
	@echo "Step 1 — Update both domains in Pulumi.$(STACK).yaml:"
	@echo "  $(PULUMI_PROJECT):domain: app.newdomain.com"
	@echo "  $(PULUMI_PROJECT):api_domain: api.newdomain.com"
	@echo ""
	@echo "Step 2 — Apply infra:"
	@echo "  make up"
	@echo ""
	@echo "  What this does:"
	@echo "    - Recreates the GCS bucket (must match domain — old bucket deleted)"
	@echo "    - Replaces the SSL cert to cover the new domains"
	@echo "    - Updates CORS_ORIGINS on Cloud Run to the new frontend domain"
	@echo "    - Updates URL map host rules"
	@echo "  Expect brief HTTPS disruption while the new cert provisions."
	@echo "  Frontend will be down until step 5 (bucket recreated but empty)."
	@echo ""
	@echo "Step 3 — Get the load balancer IP:"
	@echo "  make outputs | grep frontend_ip"
	@echo ""
	@echo "Step 4 — Update DNS at your registrar (DNS-only mode, not proxied):"
	@echo "  A  app.newdomain.com  →  <frontend_ip from step 3>"
	@echo "  A  api.newdomain.com  →  <frontend_ip from step 3>"
	@echo "  Remove old A records for the previous domain."
	@echo ""
	@echo "Step 5 — Redeploy frontend (syncs assets to new bucket, bakes new API URL):"
	@echo "  make deploy-frontend"
	@echo ""
	@echo "Step 6 — Wait for SSL cert to provision (~10-30 min after DNS propagates):"
	@echo "  make status"
	@echo "  Watch managed.status → ACTIVE for both new domains."
	@echo ""
	@echo "Step 7 — Verify:"
	@echo "  curl https://app.newdomain.com"
	@echo "  curl https://api.newdomain.com/health"
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

# Full stack teardown — destroys all GCP resources for this stack.
#
# Why not just `pulumi destroy`?
# GCP enforces strict deletion ordering that Pulumi can't always infer:
#   1. Cloud Run holds a serverless VPC address reservation in the subnet.
#      GCP won't delete the subnet until Cloud Run is gone AND the reservation
#      is released — which takes ~30s after Cloud Run deletion. If Pulumi tries
#      to delete the subnet in parallel it fails.
#   2. Cloud SQL holds a reference to the VPC peering connection. GCP won't
#      delete the peering until SQL is fully gone. Again, async on GCP's side.
#
# This target pre-deletes the two blocking resources manually before handing
# off to `pulumi destroy`, giving GCP time to release its internal references.
# The frontend LB ordering (forwarding rules → proxies → url maps/certs) is
# handled by explicit depends_on in frontend.py so Pulumi manages that itself.
#
# The -gcloud commands use - prefix so make continues even if already deleted.
# CAUTION: this destroys all infrastructure for the $(STACK) stack.
.PHONY: destroy
destroy:
	@echo ""
	@echo "=== Destroying $(STACK) stack ==="
	@echo ""
	@echo "Step 1/4: Deleting Cloud Run service + job (releases VPC address reservation)..."
	-gcloud run services delete $(PREFIX)-backend \
		--region $(REGION) --project $(PROJECT) --quiet 2>/dev/null
	-gcloud run jobs delete $(PREFIX)-migrate \
		--region $(REGION) --project $(PROJECT) --quiet 2>/dev/null
	@echo ""
	@echo "Step 2/4: Waiting 30s for GCP to release serverless VPC address..."
	@sleep 30
	@echo ""
	@echo "Step 3/4: Deleting Cloud SQL instance (releases VPC peering reference)..."
	-gcloud sql instances delete $(PREFIX)-postgres \
		--project $(PROJECT) --quiet 2>/dev/null
	@echo ""
	@echo "Step 4/4: Waiting 30s for Cloud SQL deletion to propagate..."
	@sleep 30
	@echo ""
	@echo "Running pulumi destroy (remaining resources)..."
	PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --stack $(STACK) --yes

# ── Status ────────────────────────────────────────────────────────────────────

# Single command to see the health of everything deployed.
# Useful after a deploy or when debugging connectivity issues.
.PHONY: status
status:
	@echo ""
	@echo "=== Cloud Run (backend) ==="
	@gcloud run services describe $(PREFIX)-backend \
		--region $(REGION) --project $(PROJECT) \
		--format="table(status.latestReadyRevisionName, status.url)" 2>&1
	@echo ""
	@echo "=== Migration Job ==="
	@gcloud run jobs describe $(MIGRATION_JOB) \
		--region $(REGION) --project $(PROJECT) \
		--format="table(metadata.name, status.conditions[0].status)" 2>&1
	@echo ""
	@echo "=== SSL Certificate ==="
	@gcloud compute ssl-certificates list \
		--filter="name~$(PREFIX)-frontend" \
		--global --project $(PROJECT) \
		--format="table(name, managed.status, managed.domainStatus)" 2>&1
	@echo ""
	@echo "=== DNS resolution ==="
	@FRONTEND_URL=$$(PULUMI_CONFIG_PASSPHRASE="" pulumi stack output frontend_url --stack $(STACK) 2>/dev/null | sed 's|https://||'); \
		dig $$FRONTEND_URL A +short 2>&1
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
# VITE_BACKEND_URL is injected from the live stack output at build time so
# it always points at the correct Cloud Run service URL. It is NOT read from
# .env.production (that file intentionally omits it) — this prevents stale
# URLs from ever being baked into a production build.
#
# Other vars (POSTHOG_URL, POSTHOG_KEY) come from .env.production as normal.
#
# --delete-unmatched-destination-objects removes stale files from previous
# builds. Critical because Vite uses content-hashed filenames (main.abc123.js)
# and old versions accumulate in the bucket without this flag, bloating
# storage and potentially serving outdated assets.
.PHONY: build-frontend
build-frontend:
	cd $(FRONTEND_DIR) && VITE_BACKEND_URL=$(SERVICE_URL) npm run build

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
	@echo "Live at: $(FRONTEND_URL)"

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
