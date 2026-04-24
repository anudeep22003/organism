# Infra Agent Reference

Quick reference for AI agents working in this directory. Read this before
touching anything. For the full reasoning behind decisions, see `DECISIONS.md`.

---

## What this is

Pulumi Python project that provisions the full GCP stack for StoryEngine.
One active stack: `main` → `app.dekatha.com`.

Runtime: Python 3.12, toolchain: `uv`. Run everything from `infra/`.

All components are `pulumi.ComponentResource` subclasses. This makes the
infra reusable — new projects get a 15-line `__main__.py` and the full
battle-tested GCP stack.

---

## File map

```
__main__.py              Wiring — instantiates all components in dependency order
Pulumi.yaml              Project definition (name, runtime, toolchain)
Pulumi.main.yaml         Stack config (project, region, image_tag, domain)
Makefile                 All operational commands — run `make help`
DECISIONS.md             Full reasoning for non-obvious choices
components/
  config.py              Single source of truth: PROJECT, REGION, PREFIX, IMAGE_TAG, DOMAIN
  storage.py             Layer 1 — class MediaBucket — GCS media bucket (private, signed URLs)
  iam.py                 Layers 2+5 — class LocalhostServiceAccount, class CloudRunServiceAccount
  registry.py            Layer 3 — class DockerRegistry — Artifact Registry Docker repo
  secrets.py             Layer 4 — class AppSecrets — Secret Manager containers (slots only)
  networking.py          Layer 6 — class Network — VPC, subnet, private services peering
  database.py            Layer 7 — class Database — Cloud SQL Postgres 16, private IP, random password
  cloudrun.py            Layer 8 — class CloudRunService — Cloud Run service (backend)
  migrations.py          Layer 9 — class MigrationJob — Cloud Run Job (alembic upgrade head)
  frontend.py            Layer 8b — class Frontend — GCS bucket + Global LB + SSL cert + HTTP redirect
  ci.py                  Layer 10 — class CiResources — github-actions-sa + Workload Identity Federation
scripts/
  populate-secrets.sh    Push .env.local secrets to Secret Manager (idempotent)
keys/
  *.json                 SA key files — gitignored, never commit
```

---

## Layer order in `__main__.py`

Order matters — later layers depend on earlier ones. All dependencies are
passed explicitly via keyword arguments so Pulumi sequences operations correctly.

```
1   storage         MediaBucket("storage")
2   iam (localhost)  LocalhostServiceAccount("localhost-sa", bucket=storage.bucket)
3   registry        DockerRegistry("registry")
4   secrets         AppSecrets("secrets")
5   iam (cloudrun)  CloudRunServiceAccount("cloudrun-sa", bucket=..., registry=..., secrets=...)
6   networking      Network("network")
7   database        Database("db", vpc=..., peering=..., secrets=...)
    __main__        Write DATABASE_URL SecretVersion (cross-component wiring)
8a  cloudrun        CloudRunService("backend", sa=..., secrets=..., registry_url=..., vpc=..., subnet=...)
9   migrations      MigrationJob("migrations", sa=..., secrets=..., registry_url=..., vpc=..., subnet=...)
8b  frontend        Frontend("frontend", service=service.service)
10  ci              CiResources("ci", registry=..., cloudrun_sa=..., frontend_bucket=...)
```

---

## ComponentResource pattern

Every component follows this structure:

```python
class MyComponent(pulumi.ComponentResource):
    """Docstring with: what it creates, what it exposes, why."""

    # Type annotations for exposed attributes
    some_resource: gcp.SomeResource
    some_output: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        dependency: gcp.SomeOtherResource,      # explicit, named dependencies
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:MyComponent", name, {}, opts)

        # Every child resource MUST have opts=pulumi.ResourceOptions(parent=self)
        self.some_resource = gcp.SomeResource(
            f"{name}-resource",           # logical name: {name}-suffix
            name=resource_name("gcp-name"),  # GCP resource name: unchanged
            ...,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # If a resource already has depends_on, merge parent= in:
        other_resource = gcp.Other(
            f"{name}-other",
            ...,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.some_resource]),
        )

        self.register_outputs({
            "some_resource": self.some_resource,
            "some_output": self.some_output,
        })
```

**Critical rules:**
1. Every `gcp.*` resource inside `__init__` needs `opts=pulumi.ResourceOptions(parent=self)`
2. `register_outputs({...})` must be called at the end of every `__init__`
3. Logical names use `f"{name}-suffix"` (component-scoped, not hardcoded)
4. GCP resource `name=` stays as `resource_name("...")` — never change these
5. Every `__init__` accepts `opts: pulumi.ResourceOptions | None = None`

---

## Naming conventions

All GCP resource names use `PREFIX = f"storyengine-{stack}"` — currently `storyengine-main`.

```python
from components.config import PREFIX, resource_name

resource_name("backend")   # → "storyengine-main-backend"
resource_name("migrate")   # → "storyengine-main-migrate"
f"{PREFIX}-some-secret"    # → "storyengine-main-some-secret"
```

Pulumi logical names (what appears in `pulumi up` output) use `f"{name}-suffix"` where
`name` is the instance name passed to the component. GCP resource names and Pulumi
logical names are completely decoupled.

**Image tags:** always git SHA, never `latest`. The SHA is stamped into
`Pulumi.main.yaml` via `pulumi config set image_tag <sha>` before every deploy.

---

## How to add a new secret (e.g. Stripe API key)

**Starting a new project?** `secrets.py`, `iam.py`, and `cloudrun.py` each contain
three StoryEngine-specific secrets (`anthropic_api_key`, `openai_api_key`, `fal_api_key`)
clearly labelled with comments. Delete those three from each file and add your own
using the exact same pattern shown below. The steps are identical whether you are
replacing the examples or adding to an existing project.

Every secret requires the same three-file change — no exceptions. An agent that
updates only one or two of the three files will produce a broken deployment:
- Missing from `secrets.py` → no GCP slot → `make up` fails
- Missing from `iam.py` → Cloud Run cannot read the secret → container crashes on startup
- Missing from `cloudrun.py` → secret never injected as env var → `os.getenv()` returns `None`

### Step 1 — `components/secrets.py`

Add a new secret container to `AppSecrets.__init__`:

```python
self.stripe_api_key = _make_secret(
    f"{name}-stripe-api-key",
    f"{PREFIX}-stripe-api-key",
    parent=self,
)
```

### Step 2 — `components/iam.py` → `CloudRunServiceAccount.__init__`

Grant `cloudrun-sa` access to read the new secret:

```python
gcp.secretmanager.SecretIamMember(
    f"{name}-stripe-accessor",
    secret_id=secrets.stripe_api_key.secret_id,
    role="roles/secretmanager.secretAccessor",
    member=member,
    opts=pulumi.ResourceOptions(parent=self),
)
```

### Step 3 — `components/cloudrun.py` → `CloudRunService.__init__`

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
skip Secret Manager entirely. Add directly to the `plain_env_vars` dict in
`CloudRunService.__init__` in `components/cloudrun.py`:

```python
"SOME_CONFIG_VALUE": "the-value",
```

Then `make up` — no `populate-secrets`, no IAM changes needed.

Runtime origin config follows this pattern too. For StoryEngine auth rollout,
`FRONTEND_URL` and `API_URL` are plain env vars managed by Pulumi, while the
auth credentials (`GOOGLE_OAUTH_CLIENT_SECRET`, `JWT_SECRET_KEY`,
`AUTH_SESSION_SECRET`, `FERNET_ENCRYPTION_KEY`) remain Secret Manager values
populated via `make populate-secrets`.

---

## How the DB password is generated and wired

This is the pattern for any credential that must be auto-generated:

```python
# components/database.py — inside Database.__init__
password = random.RandomPassword(
    f"{name}-password",
    length=32,
    special=False,
    opts=pulumi.ResourceOptions(parent=self),
)

# Store raw password in Secret Manager (retrievable for debugging)
gcp.secretmanager.SecretVersion(
    f"{name}-password-version",
    secret=secrets.db_password.id,
    secret_data=password.result,
    opts=pulumi.ResourceOptions(parent=self),
)

# Construct DATABASE_URL from private IP + generated password
self.database_url = pulumi.Output.all(
    self.instance.private_ip_address, password.result
).apply(
    lambda args: f"postgresql+psycopg://appuser:{args[1]}@{args[0]}:5432/storyengine"
)
```

Then in `__main__.py`, after the database is created:

```python
# Cross-component wiring: depends on BOTH db.database_url AND secrets.database_url.id
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

Pattern: one file per component, one `ComponentResource` class, wire in `__main__.py`.

1. **Create `components/redis.py`**

```python
import pulumi
import pulumi_gcp as gcp
from components.config import APP, REGION, resource_name

class Redis(pulumi.ComponentResource):
    instance: gcp.redis.Instance

    def __init__(self, name: str, vpc: gcp.compute.Network,
                 opts: pulumi.ResourceOptions | None = None) -> None:
        super().__init__(f"{APP}:infra:Redis", name, {}, opts)

        self.instance = gcp.redis.Instance(
            f"{name}-instance",
            name=resource_name("redis"),
            tier="BASIC",
            memory_size_gb=1,
            region=REGION,
            authorized_network=vpc.id,
            opts=pulumi.ResourceOptions(parent=self),
        )
        self.register_outputs({"instance": self.instance})
```

2. **Wire in `__main__.py`** — after networking (Layer 6), before Cloud Run (Layer 8):

```python
from components.redis import Redis
redis = Redis("redis", vpc=network.vpc)
```

3. **Pass the Redis host to Cloud Run** via `plain_env_vars` in `CloudRunService.__init__`:

```python
"REDIS_HOST": redis.instance.host,   # Pulumi Output[str] — resolved at deploy time
```

4. **Export the output** if useful:

```python
pulumi.export("redis_host", redis.instance.host)
```

Any resource that needs VPC access follows the same pattern as Cloud SQL:
provision after the VPC peering connection is established. Pass `peering_connection`
in `depends_on` if Pulumi can't infer the dependency.

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
api_url` at frontend build time — never from `.env.production`.

---

## Key decisions — the ones you'll get wrong without this

**`VITE_BACKEND_URL` is not in `.env.production`**
Deliberately omitted. It is injected at build time from `pulumi stack output
api_url`. Hardcoding it produces stale URLs when the stack is rebuilt.

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

**Frontend and API share one load balancer (cost decision)**
`app.dekatha.com` (GCS) and `api.dekatha.com` (Cloud Run) share one Global IP,
one SSL cert, and one set of forwarding rules via URL map host-based routing.
A dedicated API LB costs ~$36/month extra (two additional forwarding rules).
To decouple: extract the NEG + BackendService + new GlobalAddress + new SSL cert
+ new URLMap + new forwarding rules into `components/backend_lb.py`, remove the
api host_rule and path_matcher from `frontend.py`, update DNS with a new A record.

**Cloud Run Job for migrations, not Auth Proxy**
GitHub Actions runners are outside the VPC. Cloud SQL has a private IP only.
The migration job runs inside the VPC via direct VPC egress. CI triggers it
with `gcloud run jobs execute ... --wait` and reads the exit code.

**`max_retries=0` on the migration job**
A failed migration leaves the schema in a partially-applied state. Automatic
retries make this worse. Fail fast, alert a human.

**DATABASE_URL SecretVersion lives in `__main__.py`, not in `Database`**
It depends on both `db.database_url` (from `Database`) and `secrets.database_url.id`
(from `AppSecrets`). Cross-component wiring belongs at the orchestration level.

**`iam.py` has two separate classes, not one**
`LocalhostServiceAccount` and `CloudRunServiceAccount` have different dependencies
and different lifecycles. A future project might want `LocalhostServiceAccount`
without `CloudRunServiceAccount`. Keep them separate.

---

## Using this as a template for a new project

Clone this repo and follow the steps below. All project-specific values flow
from two YAML files — no component code changes are needed for a standard stack.

### Step 1 — Edit `Pulumi.yaml`

Two lines to change:

```yaml
name: myapp-infra                    # was: storyengine-infra
  storyengine-infra:app: storyengine # → myapp-infra:app: myapp
```

The `name:` field drives the config key namespace everywhere — in the Makefile,
in `Pulumi.<stack>.yaml`, and in the Pulumi state. Change it first, before
anything else.

No other changes to `Pulumi.yaml` are needed. The Makefile reads `name:`
automatically — no Makefile edits required.

### Step 2 — Generate your stack config

```bash
make init-project
```

This generates `Pulumi.main.yaml` with:
- The correct key prefix derived from your updated `Pulumi.yaml`
- An auto-generated `media_bucket_suffix` (so you don't have to run `openssl rand -hex 2`)
- `<...>` placeholders for every value you need to supply

See `Pulumi.main.yaml.example` for a fully annotated reference of every key.

### Step 3 — Fill in the generated file

Open `Pulumi.main.yaml` and replace every `<...>` placeholder:

| Key | What to put |
|-----|-------------|
| `gcp:project` | Your GCP project ID |
| `gcp:region` | Your preferred region (e.g. `europe-west2`) |
| `app` | Your app name — lowercase, no spaces |
| `domain` | Frontend domain (e.g. `app.myapp.com`) |
| `api_domain` | API domain (e.g. `api.myapp.com`) |
| `github_repo` | Your GitHub repo as `owner/repo` — **security-critical** |
| `media_bucket_suffix` | Already filled in — do not change it again after first deploy |
| `image_tag` | Leave as `latest` — overwritten by `make deploy-backend` |

### Step 4 — Create a GCS state bucket

Pulumi needs somewhere to store its state. This bucket lives outside Pulumi
(it predates any stack) so you create it manually once:

```bash
gcloud storage buckets create gs://myapp-pulumi-state \
  --project <your-gcp-project> \
  --location <your-region>
export PULUMI_BACKEND_URL=gs://myapp-pulumi-state
```

Add `PULUMI_BACKEND_URL` as a repository variable (not secret) in GitHub Actions:
Settings → Secrets and variables → Actions → Variables.

### Step 5 — Update `__main__.py` for your secrets

The existing `__main__.py` wires `AppSecrets` with StoryEngine's three API key slots
(`anthropic_api_key`, `openai_api_key`, `fal_api_key`). Replace these with your
own secrets — or remove them entirely if your app has different external dependencies.

Everything else in `__main__.py` (storage, IAM, networking, database, Cloud Run,
migrations, frontend, CI) is generic and needs no changes for a standard stack.

### Step 6 — Init the stack and deploy

```bash
pulumi stack init main
make up       # provisions all GCP resources (~5 min on first run)
make setup    # prints remaining developer onboarding steps
```

### Reference: full `__main__.py` shape

```python
from components.ci import CiResources
from components.cloudrun import CloudRunService
from components.config import MEDIA_BUCKET_NAME
from components.database import Database
from components.frontend import Frontend
from components.iam import CloudRunServiceAccount, LocalhostServiceAccount
from components.migrations import MigrationJob
from components.networking import Network
from components.registry import DockerRegistry
from components.secrets import AppSecrets
from components.storage import MediaBucket
import pulumi, pulumi_gcp as gcp

storage = MediaBucket("storage")
localhost_sa = LocalhostServiceAccount("localhost-sa", bucket=storage.bucket)
registry = DockerRegistry("registry")
secrets = AppSecrets("secrets")
cloudrun_sa = CloudRunServiceAccount("cloudrun-sa", bucket=storage.bucket,
                                     registry=registry.repository, secrets=secrets)
network = Network("network")
db = Database("db", vpc=network.vpc, peering=network.peering_connection, secrets=secrets)
gcp.secretmanager.SecretVersion("database-url-version",
    secret=secrets.database_url.id, secret_data=db.database_url)
service = CloudRunService("backend", sa=cloudrun_sa.account, secrets=secrets,
                          registry_url=registry.url, vpc=network.vpc, subnet=network.subnet)
migrations = MigrationJob("migrations", sa=cloudrun_sa.account, secrets=secrets,
                          registry_url=registry.url, vpc=network.vpc, subnet=network.subnet)
frontend = Frontend("frontend", service=service.service)
ci = CiResources("ci", registry=registry.repository,
                 cloudrun_sa=cloudrun_sa.account, frontend_bucket=frontend.bucket)

pulumi.export("service_url", service.url)
pulumi.export("frontend_url", frontend.url)
pulumi.export("registry_url", registry.url)
# add any other outputs you need
```

---

## What NOT to touch

| Thing | Why |
|---|---|
| `my-app-pulumi-state` GCS bucket | Predates Pulumi, stores stack state — never manage via Pulumi |
| `DATABASE_URL` in `.env.local` | Must stay in `# --- variables ---`, never `# --- secrets ---` |
| `.github/workflows/ci.yml` trigger | PR-only by design — `deploy.yml` owns `main` |
| `Pulumi.main.yaml` `image_tag` | Set automatically by `make deploy-backend` and CI — don't edit manually |
| GCP resource names (`resource_name()` calls) | Stable across refactors — changing them recreates GCP resources |

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
