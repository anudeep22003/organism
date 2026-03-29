# Infra Agent Reference

Quick reference for AI agents working in this directory. Read this before
touching anything. For the full reasoning behind decisions, see `DECISIONS.md`.

---

## What this is

Pulumi Python project that provisions the full GCP stack for StoryEngine.
One active stack: `main` → `app.dekatha.com`.

Runtime: Python 3.12, toolchain: `uv`. Run everything from `infra/`.

---

## File map

```
__main__.py              Wiring — imports and calls all components in order
Pulumi.yaml              Project definition (name, runtime, toolchain)
Pulumi.main.yaml         Stack config (project, region, image_tag, domain)
Makefile                 All operational commands — run `make help`
DECISIONS.md             Full reasoning for non-obvious choices
components/
  config.py              Single source of truth: PROJECT, REGION, PREFIX, IMAGE_TAG, DOMAIN
  storage.py             Layer 1 — GCS media bucket (private, signed URLs)
  iam.py                 Layers 2+5 — localhost-sa, cloudrun-sa, all IAM bindings
  registry.py            Layer 3 — Artifact Registry Docker repo
  secrets.py             Layer 4 — Secret Manager containers (slots only, not values)
  networking.py          Layer 6 — VPC, subnet, private services peering
  database.py            Layer 7 — Cloud SQL Postgres 16, private IP, random password
  cloudrun.py            Layer 8 — Cloud Run service (backend)
  migrations.py          Layer 9 — Cloud Run Job (alembic upgrade head)
  frontend.py            Layer 8 — GCS bucket + Global LB + SSL cert + HTTP redirect
  ci.py                  Layer 10 — github-actions-sa + Workload Identity Federation
scripts/
  populate-secrets.sh    Push .env.local secrets to Secret Manager (idempotent)
keys/
  *.json                 SA key files — gitignored, never commit
```

---

## Layer order in `__main__.py`

Order matters — later layers depend on earlier ones. Pass dependencies
explicitly so Pulumi sequences operations correctly.

```
1   storage       GCS media bucket
2   iam           localhost-sa (needs bucket)
3   registry      Artifact Registry repo
4   secrets       Secret Manager containers
5   iam           cloudrun-sa (needs bucket, registry, secrets)
6   networking    VPC + subnet + peering
7   database      Cloud SQL (needs VPC + peering + secrets)
    __main__      Write DATABASE_URL SecretVersion (needs db output)
8   cloudrun      Cloud Run service (needs SA, secrets, registry_url, vpc, subnet)
9   migrations    Cloud Run Job (needs SA, secrets, registry_url, vpc, subnet)
8   frontend      GCS + LB + SSL (no dependencies)
10  ci            github-actions-sa + WIF (needs registry, cloudrun_sa, frontend.bucket)
```

---

## Naming conventions

All resource names use `PREFIX = f"storyengine-{stack}"` — currently `storyengine-main`.

```python
from components.config import PREFIX, resource_name

resource_name("backend")   # → "storyengine-main-backend"
resource_name("migrate")   # → "storyengine-main-migrate"
f"{PREFIX}-some-secret"    # → "storyengine-main-some-secret"
```

Use `resource_name()` for GCP resource names. Use `f"{PREFIX}-..."` for
Secret Manager secret IDs and bucket names. Never hardcode `storyengine-main`.

**Image tags:** always git SHA, never `latest`. The SHA is stamped into
`Pulumi.main.yaml` via `pulumi config set image_tag <sha>` before every deploy.

---

## How to add a new secret (e.g. Stripe API key)

### Step 1 — `components/secrets.py`

Add a new secret container to `AppSecrets.__init__`:

```python
self.stripe_api_key = _make_secret(
    "secret-stripe-api-key",
    f"{PREFIX}-stripe-api-key",
)
```

### Step 2 — `components/iam.py` → `create_cloudrun_sa()`

Grant `cloudrun-sa` access to read the new secret:

```python
gcp.secretmanager.SecretIamMember(
    "cloudrun-sa-stripe-accessor",
    secret_id=secrets.stripe_api_key.secret_id,
    role="roles/secretmanager.secretAccessor",
    member=member,
)
```

### Step 3 — `components/cloudrun.py` → `create_cloudrun_service()`

Add to `secret_env_vars`:

```python
gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
    name="STRIPE_API_KEY",
    value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
        secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
            secret=secrets.stripe_api_key.secret_id,
            version="latest",
        ),
    ),
),
```

Also pass `secrets.stripe_api_key` through the function signature if needed.

### Step 4 — Apply infra

```bash
make up   # provisions the Secret Manager container + IAM binding + Cloud Run wiring
```

### Step 5 — Push the value

Add to `backend/.env.local` under `# --- secrets ---`:

```
STRIPE_API_KEY=sk_live_...
```

Then:

```bash
make populate-secrets
```

### Step 6 — Redeploy to pick up the new secret

```bash
make deploy-backend   # new Cloud Run revision fetches the secret at startup
```

---

## How to add a plain env var (non-secret)

For values that aren't sensitive (project IDs, bucket names, feature flags),
skip Secret Manager entirely. Add directly to `plain_env_vars` in
`components/cloudrun.py`:

```python
"SOME_CONFIG_VALUE": "the-value",
```

Then `make up` — no `populate-secrets`, no IAM changes needed.

---

## How the DB password is generated and wired

This is the pattern for any credential that must be auto-generated:

```python
# components/database.py
password = random.RandomPassword("db-password", length=32, special=False)

# Store raw password in Secret Manager (retrievable for debugging)
gcp.secretmanager.SecretVersion(
    "db-password-version",
    secret=secrets.db_password.id,
    secret_data=password.result,
)

# Construct DATABASE_URL from the private IP + generated password
# and write it as a SecretVersion — Cloud Run reads this at startup
database_url = pulumi.Output.concat(
    "postgresql+psycopg://postgres:",
    password.result,
    "@", instance.private_ip_address,
    "/postgres"
)
```

Then in `__main__.py`, after the database is created:

```python
gcp.secretmanager.SecretVersion(
    "database-url-version",
    secret=secrets.database_url.id,
    secret_data=db.database_url,
)
```

Key point: `DATABASE_URL` is owned by Pulumi. It is constructed from the
live Cloud SQL IP and generated password. It must never be manually managed.
See `.env.local` structure below.

---

## `backend/.env.local` structure

`populate-secrets.sh` reads this file and only uploads keys in the
`# --- secrets ---` section. Everything under `# --- variables ---` is
ignored by the script.

```bash
# --- secrets ---
ANTHROPIC_API_KEY=...      ← uploaded to Secret Manager
OPENAI_API_KEY=...         ← uploaded to Secret Manager
FAL_API_KEY=...            ← uploaded to Secret Manager
# DATABASE_URL goes here if you add it — but DON'T. See below.

# --- variables ---
DATABASE_URL=postgresql+psycopg://postgres:123456@localhost:5432/mydb  ← local only, NOT uploaded
GCP_PROJECT_ID=shared-apps-infrastructure
GCP_REGION=europe-west2
GCP_STORAGE_BUCKET=storyengine-main-media-x7k2
GOOGLE_APPLICATION_CREDENTIALS=/path/to/infra/keys/main-localhost-sa-key.json
```

**Critical:** `DATABASE_URL` must always stay in `# --- variables ---`.
If it ends up in `# --- secrets ---`, `make populate-secrets` will overwrite
the Cloud SQL URL (written by Pulumi) with the local Postgres URL — Cloud Run
silently breaks on the next cold start.

---

## How to add a new GCP resource (e.g. Redis / Memorystore)

Pattern: one file per layer, one `create_*()` function, wire in `__main__.py`.

1. **Create `components/redis.py`**

```python
import pulumi_gcp as gcp
from components.config import PROJECT, REGION, resource_name

def create_redis(vpc: gcp.compute.Network):
    instance = gcp.redis.Instance(
        "redis",
        name=resource_name("redis"),
        tier="BASIC",
        memory_size_gb=1,
        region=REGION,
        authorized_network=vpc.id,
    )
    return instance
```

2. **Wire in `__main__.py`** — after networking (Layer 6), before Cloud Run (Layer 8):

```python
from components.redis import create_redis
redis = create_redis(vpc)
```

3. **Pass the Redis host to Cloud Run** via `plain_env_vars` in `cloudrun.py`:

```python
"REDIS_HOST": redis.host,   # Pulumi Output[str] — resolved at deploy time
```

4. **Export the output** if useful:

```python
pulumi.export("redis_host", redis.host)
```

Any resource that needs VPC access follows the same pattern as Cloud SQL:
it must be provisioned after the VPC peering connection is established.
Pass `peering_connection` in `depends_on` if Pulumi can't infer the dependency.

---

## Reading live values from the stack

Never hardcode URLs, bucket names, or IPs that come from Pulumi outputs.
Read them at runtime:

```bash
# From the terminal
pulumi stack output service_url --stack main
pulumi stack output frontend_bucket --stack main
pulumi stack output db_private_ip --stack main

# Full list
make outputs
```

In Python code outside Pulumi (e.g. scripts), use:

```bash
PULUMI_CONFIG_PASSPHRASE="" pulumi stack output service_url --stack main
```

In the CI pipeline, `VITE_BACKEND_URL` is injected from `pulumi stack output
service_url` at frontend build time — never from `.env.production`.

---

## Key decisions — the ones you'll get wrong without this

**`VITE_BACKEND_URL` is not in `.env.production`**
Deliberately omitted. It is injected at build time from `pulumi stack output
service_url`. Hardcoding it produces stale URLs when the stack is rebuilt.

**`.venv/bin/uvicorn`, not `uv run uvicorn` in Dockerfile**
`uv run` checks venv freshness at every startup and re-syncs if stale —
inside a container this triggers a full package download, causing OOM and
slow cold starts. The venv is built correctly at image build time. Call
uvicorn directly from the venv.

**`PULUMI_BACKEND_URL` is a GitHub Actions variable, not a secret**
Value: `gs://my-app-pulumi-state`. Must be set as a repository *variable*
(not secret) under Settings → Secrets and variables → Actions → Variables.
Pulumi defaults to Pulumi Cloud in non-interactive sessions — this env var
overrides that. It cannot be read from Pulumi itself (chicken-and-egg).

**`my-app-pulumi-state` bucket is not managed by Pulumi**
It predates the stack — it's where the stack state is stored. Never add it
to `__main__.py` or any component. Pulumi cannot manage the bucket that
stores its own state.

**`roles/editor` for `github-actions-sa` is intentional**
Pulumi manages 10+ resource types across the project. Enumerating individual
roles is high-maintenance and breaks whenever a new resource type is added.
`roles/editor` excludes IAM permissions — the SA cannot escalate its own
privileges.

**Cloud Run Job for migrations, not Auth Proxy**
GitHub Actions runners are outside the VPC. Cloud SQL has a private IP only.
The migration job runs inside the VPC via direct VPC egress. CI triggers it
with `gcloud run jobs execute ... --wait` and reads the exit code.

**`max_retries=0` on the migration job**
A failed migration leaves the schema in a partially-applied state. Automatic
retries make this worse. Fail fast, alert a human.

---

## What NOT to touch

| Thing | Why |
|---|---|
| `my-app-pulumi-state` GCS bucket | Predates Pulumi, stores stack state — never manage via Pulumi |
| `DATABASE_URL` in `.env.local` | Must stay in `# --- variables ---`, never `# --- secrets ---` |
| `.github/workflows/ci.yml` trigger | PR-only by design — `deploy.yml` owns `main` |
| `Pulumi.main.yaml` `image_tag` | Set automatically by `make deploy-backend` and CI — don't edit manually |

---

## Operational quick reference

```bash
make help              # full list of targets

make preview           # dry run — what would pulumi up change?
make up                # apply infra changes only (no image rebuild)
make outputs           # print all stack outputs

make deploy-backend    # build image → push → pulumi up
make deploy-frontend   # build frontend (injects service_url) → rsync to GCS
make deploy-all        # both, backend first

make migrate           # trigger Cloud Run migration job, wait for exit code
make populate-secrets  # push .env.local secrets to Secret Manager
make rotate-secrets    # populate-secrets + deploy-backend (picks up new values)

make status            # Cloud Run revision, SSL cert state, DNS, stack outputs
make proxy             # Cloud SQL Auth Proxy on localhost:5433 (inspection only)
```
