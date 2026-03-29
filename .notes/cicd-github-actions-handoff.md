# CI/CD Pipeline — GitHub Actions Handoff

**Status:** Not yet built. All prerequisites are in place. This document tells the next agent exactly what to build and why.

---

## What Exists Today (Manual Deploy)

The full deployment flow works manually from a developer's laptop:

```
make deploy-backend    # build Docker image → push to Artifact Registry → pulumi up
make migrate           # trigger Cloud Run Job → alembic upgrade head (inside VPC)
make deploy-frontend   # npm build → gcloud storage rsync to GCS bucket
```

The goal is to automate this on push to `dev` (and later `main`) via GitHub Actions.

---

## What Already Exists in GitHub Actions

`.github/workflows/ci.yml` runs on **all PRs and pushes to `main`**:
- Backend: `ruff check`, `mypy` (pytest commented out)
- Frontend: `type-check`, `npm run build`

**This file must not be changed.** The new deploy workflow is a separate file.

---

## Infrastructure Already in Place

Everything the CI/CD pipeline needs already exists in GCP. Nothing new needs to be provisioned except a `github-actions-sa` service account and Workload Identity Federation (see below).

### GCP Project
- **Project ID:** `shared-apps-infrastructure`
- **Region:** `europe-west2`

### Artifact Registry
- **Registry URL:** `europe-west2-docker.pkg.dev/shared-apps-infrastructure/storyengine-dev`
- **Backend image tag pattern:** `<registry>/backend:<git-sha>`
- Image SHA is stamped into Pulumi config (`image_tag`) before `pulumi up`

### Cloud Run Service
- **Name:** `storyengine-dev-backend`
- **URL:** `https://storyengine-dev-backend-aojdjt3wia-nw.a.run.app`
- Managed by Pulumi — `pulumi up` updates it with the new image tag

### Cloud Run Migration Job
- **Name:** `storyengine-dev-migrate`
- Runs `alembic upgrade head` inside the VPC using the same backend image
- Triggered with: `gcloud run jobs execute storyengine-dev-migrate --region europe-west2 --project shared-apps-infrastructure --wait`
- Exits 0 on success, non-zero on failure — CI can depend on the exit code
- Only has `DATABASE_URL` as a secret — intentional, it reads from `os.environ` directly

### Pulumi State
- **Backend:** `gs://storyengine-infra-state` (GCS bucket)
- **Stack:** `dev`
- **Passphrase:** empty string (`""`) — must be set as `PULUMI_CONFIG_PASSPHRASE=""` in CI
- Stack config lives in `infra/Pulumi.dev.yaml` — the key field is `image_tag`

### Frontend
- **GCS bucket:** `dev.dekatha.com`
- **Frontend dir:** `frontend/` — built with `npm run build`, outputs to `frontend/dist/`
- Synced with: `gcloud storage rsync frontend/dist/ gs://dev.dekatha.com --recursive --delete-unmatched-destination-objects`

### Service Accounts in Use
- `cloudrun-sa@shared-apps-infrastructure.iam.gserviceaccount.com` — runs the Cloud Run service and migration job. Already has all necessary permissions.
- `localhost-sa@shared-apps-infrastructure.iam.gserviceaccount.com` — developer laptops only, not relevant to CI.

---

## What Needs to Be Built

### Step 1: Create `github-actions-sa` in Pulumi

Add a new service account to `infra/components/iam.py` (or a new `infra/components/ci.py`).

**Permissions needed:**

| Role | Scope | Why |
|---|---|---|
| `roles/artifactregistry.writer` | The `storyengine-dev` repository | Push Docker images |
| `roles/run.developer` | Project | Update Cloud Run service, trigger Cloud Run Jobs |
| `roles/storage.objectAdmin` | `dev.dekatha.com` bucket | Sync frontend files |
| `roles/iam.serviceAccountUser` | `cloudrun-sa` | Pulumi can deploy services that run as cloudrun-sa |
| `roles/editor` | Project | Pulumi needs broad permissions to manage all stack resources |

The `roles/editor` is broad but scoped to the project. The alternative is enumerating 20+ individual roles for Pulumi — high maintenance. `roles/editor` is standard for CI service accounts running IaC tools.

Export the SA email as a stack output for use when setting up Workload Identity.

### Step 2: Set Up Workload Identity Federation in Pulumi

Workload Identity Federation lets GitHub Actions authenticate to GCP without a JSON key file. GitHub generates a short-lived OIDC token; GCP exchanges it for a temporary access token scoped to `github-actions-sa`.

Add to Pulumi (same file as the SA, or `infra/components/ci.py`):

```python
# Workload Identity Pool
pool = gcp.iam.WorkloadIdentityPool(
    "github-actions-pool",
    workload_identity_pool_id="github-actions-pool",
    display_name="GitHub Actions",
)

# OIDC Provider for GitHub
provider = gcp.iam.WorkloadIdentityPoolProvider(
    "github-actions-provider",
    workload_identity_pool_id=pool.workload_identity_pool_id,
    workload_identity_pool_provider_id="github-actions-provider",
    display_name="GitHub Actions OIDC",
    oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
        issuer_uri="https://token.actions.githubusercontent.com",
    ),
    attribute_mapping={
        "google.subject": "assertion.sub",
        "attribute.repository": "assertion.repository",
        "attribute.ref": "assertion.ref",
    },
    # Only tokens from this specific repo can authenticate
    attribute_condition='attribute.repository == "anomalyco/organism"',
)

# Allow the pool to impersonate github-actions-sa
gcp.serviceaccount.IAMMember(
    "github-actions-wi-binding",
    service_account_id=github_actions_sa.name,
    role="roles/iam.workloadIdentityUser",
    member=pool.name.apply(
        lambda pool_name: f"principalSet://iam.googleapis.com/{pool_name}/attribute.repository/anomalyco/organism"
    ),
)
```

Export two stack outputs:
- `workload_identity_provider` — the full provider resource name (used in the workflow YAML)
- `github_actions_sa_email` — the SA email (used in the workflow YAML)

Run `pulumi up` to create these resources, then copy the output values into GitHub Secrets (see Step 4).

### Step 3: Write `.github/workflows/deploy.yml`

**Trigger:** push to `dev` or `main` branch only (not PRs).

**Structure:**

```yaml
name: Deploy

on:
  push:
    branches: [dev, main]

jobs:
  ci:
    # Reuse the existing CI checks — don't deploy broken code.
    # This runs ruff, mypy, type-check, frontend build.
    uses: ./.github/workflows/ci.yml

  deploy:
    needs: ci       # only runs if CI passes
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write   # required for Workload Identity OIDC token

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker europe-west2-docker.pkg.dev --quiet

      - name: Set image tag
        run: echo "SHA=$(git rev-parse --short HEAD)" >> $GITHUB_ENV

      - name: Build backend image
        run: |
          docker build --platform linux/amd64 \
            -t europe-west2-docker.pkg.dev/shared-apps-infrastructure/storyengine-dev/backend:${{ env.SHA }} \
            ./backend

      - name: Push backend image
        run: |
          docker push \
            europe-west2-docker.pkg.dev/shared-apps-infrastructure/storyengine-dev/backend:${{ env.SHA }}

      - name: Install Pulumi
        uses: pulumi/actions@v5

      - name: Pulumi up (update Cloud Run + migration job to new image)
        run: |
          pulumi config set image_tag ${{ env.SHA }} --stack dev
          pulumi up --stack dev --yes
        working-directory: infra
        env:
          PULUMI_CONFIG_PASSPHRASE: ""
          GOOGLE_APPLICATION_CREDENTIALS: ""   # Workload Identity handles auth

      - name: Run database migrations
        run: |
          gcloud run jobs execute storyengine-dev-migrate \
            --region europe-west2 \
            --project shared-apps-infrastructure \
            --wait

      - name: Install Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Build frontend
        run: npm ci && npm run build
        working-directory: frontend

      - name: Sync frontend to GCS
        run: |
          gcloud storage rsync frontend/dist/ gs://dev.dekatha.com \
            --recursive \
            --delete-unmatched-destination-objects \
            --project shared-apps-infrastructure

      - name: Summary
        run: |
          echo "### Deploy complete" >> $GITHUB_STEP_SUMMARY
          echo "- Image: \`${{ env.SHA }}\`" >> $GITHUB_STEP_SUMMARY
          echo "- Backend: https://storyengine-dev-backend-aojdjt3wia-nw.a.run.app" >> $GITHUB_STEP_SUMMARY
          echo "- Frontend: https://dev.dekatha.com" >> $GITHUB_STEP_SUMMARY
```

**Step ordering matters:**
1. Build + push image first (job definition needs to exist in registry before Pulumi references it)
2. `pulumi up` updates Cloud Run service + migration job to the new image tag
3. Migration job runs with the new image (schema updated before traffic shifts)
4. Frontend sync last (no dependency on backend revision)

### Step 4: Set GitHub Secrets

After `pulumi up` creates the Workload Identity resources, get the output values:
```bash
cd infra && pulumi stack output workload_identity_provider
cd infra && pulumi stack output github_actions_sa_email
```

Add these to the GitHub repo under Settings → Secrets and variables → Actions:

| Secret name | Value |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Output from `pulumi stack output workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT` | Output from `pulumi stack output github_actions_sa_email` |

No other secrets needed. No JSON key file. Workload Identity tokens are short-lived and expire when the workflow ends.

---

## Pipeline Flow Summary

```
Push to dev/main
      │
      ▼
ci.yml runs (ruff, mypy, type-check, frontend build)
      │ fails → pipeline stops, no deploy
      ▼
deploy.yml runs:
  1. Authenticate to GCP via Workload Identity (no key file)
  2. docker build --platform linux/amd64  (ubuntu runner, Docker pre-installed)
  3. docker push → Artifact Registry
  4. pulumi config set image_tag <sha>
  5. pulumi up --stack dev --yes → Cloud Run service + job updated
  6. gcloud run jobs execute storyengine-dev-migrate --wait → migrations
  7. npm build → frontend/dist/
  8. gcloud storage rsync → GCS bucket
  9. Post summary to GitHub Actions UI
```

---

## Key Design Decisions (for context)

**Why Cloud Run Job for migrations, not Auth Proxy in CI?**
GitHub Actions runners are outside the VPC. Cloud SQL only has a private IP (10.1.0.3). The Cloud Run Job runs inside the VPC via direct VPC egress, reaching Cloud SQL without any tunnel. CI just triggers the job and waits for the exit code.

**Why Workload Identity, not a JSON key?**
JSON keys are permanent credentials that need rotation. Workload Identity tokens are short-lived (expire when the workflow ends) and tied to the specific repo/branch. Nothing to rotate, nothing to leak.

**Why `pulumi up` before `gcloud run jobs execute`?**
The migration job's image tag must be updated to the new SHA before running migrations. If migrations ran first against the old image, they might miss new migration files added in the current commit.

**Why `PULUMI_CONFIG_PASSPHRASE=""`?**
The dev stack uses an empty passphrase. It's set as an empty environment variable, not a GitHub Secret. This is intentional — the dev stack doesn't contain sensitive values in Pulumi config (secrets are in Secret Manager, not Pulumi config).

**Why `--platform linux/amd64` on docker build?**
The GitHub Actions runner is `ubuntu-latest` (x86_64). Cloud Run requires `linux/amd64`. Without this flag, builds on Apple Silicon macs would produce ARM images that fail at startup on Cloud Run. The flag is harmless on x86 and necessary on ARM.

**Why is the frontend build repeated in deploy.yml?**
`ci.yml` builds the frontend to verify it compiles, but the built artifact is not persisted between workflow runs. `deploy.yml` rebuilds it for the actual sync. This is standard — build artifacts are ephemeral in GitHub Actions unless explicitly uploaded with `actions/upload-artifact`.

---

## Files to Create/Modify

| File | Action |
|---|---|
| `infra/components/ci.py` (or `iam.py`) | Add `github-actions-sa`, Workload Identity pool + provider |
| `infra/__main__.py` | Import and call the new CI component, export WI provider + SA email |
| `.github/workflows/deploy.yml` | New file — the deploy workflow |

**Do not modify:**
- `.github/workflows/ci.yml` — existing CI stays as-is
- `infra/components/cloudrun.py` — no changes needed
- `infra/components/migrations.py` — no changes needed

---

## Verification After Setup

```bash
# 1. Trigger by pushing to dev branch
git checkout -b dev
git push origin dev

# 2. Watch the Actions tab in GitHub
# Both ci.yml and deploy.yml should appear
# ci.yml runs first; deploy.yml waits for it

# 3. After completion, verify:
gcloud run services describe storyengine-dev-backend \
  --region europe-west2 --project shared-apps-infrastructure \
  --format "value(status.latestReadyRevisionName)"
# Should show a new revision

gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="storyengine-dev-migrate"' \
  --project shared-apps-infrastructure --limit 5 --freshness=30m
# Should show exit(0) from the migration job
```
