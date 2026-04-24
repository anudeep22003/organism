# Infrastructure Decisions

A record of non-obvious choices made during infrastructure setup.
Captures the *why* so future work doesn't relitigate settled questions.

---

## Layer 1 — Storage

### Bucket: uniform bucket-level access + public access prevention enforced
Per-object ACLs are disabled. All access is controlled via IAM bindings only.
`public_access_prevention=enforced` makes it impossible to accidentally expose
the bucket or any object publicly. All reads go through signed URLs.

### Signed URLs use the JSON key file (local), not serviceAccountTokenCreator
Two signing paths exist in GCS:
- Local signing: private key is in the JSON file, signing happens in-process, no GCP call needed.
- Remote signing: no key file, code calls IAM Credentials API to sign on its behalf — requires `serviceAccountTokenCreator`.

We use local signing for `localhost-sa`. `serviceAccountTokenCreator` is not needed
and was explicitly omitted to stay at minimum privilege. Cloud Run uses Workload
Identity (no key file) — when Cloud Run signs URLs it will need this role added.

---

## Layer 2 — IAM

### One service account per runtime environment
- `localhost-sa` — developer laptops, authenticated via JSON key file
- `cloudrun-sa` — Cloud Run service, authenticated via Workload Identity (no key file)

Each SA accumulates only the roles its runtime needs. Names reflect the runtime
identity, not the current set of permissions (permissions evolve, the identity is stable).

### Roles granted at resource level, not project level (except cloudsql.client)
All IAM bindings are scoped to the specific resource (bucket, secret, registry repo)
rather than the project. Exception: `roles/cloudsql.client` is project-level because
Cloud SQL IAM works at the project level — there is no per-instance binding.

### localhost-sa JSON key lives in infra/keys/ — gitignored
`infra/keys/*.json` is in `.gitignore`. The `keys/` directory is tracked via
`.gitkeep` so the directory exists in the repo. Never commit key files.

---

## Layer 3 — Artifact Registry

### Images tagged with git SHA, never `latest`
`latest` is a mutable pointer — it breaks traceability and makes rollbacks
ambiguous. Every pushed image is tagged with the short git SHA of HEAD.
The `make deploy` target stamps the SHA into Pulumi config automatically
before running `pulumi up`, so no manual tracking is needed.

### Build with `--platform linux/amd64`
Development machines are Apple Silicon (`arm64`). Cloud Run runs `linux/amd64`.
Without `--platform linux/amd64` the built image cannot run on Cloud Run.
Docker Desktop uses QEMU emulation to cross-compile transparently.

---

## Layer 4 — Secrets

### Pulumi manages secret containers, not secret values (except DATABASE_URL)
Pulumi creates the named slot in Secret Manager. Values are populated separately
via `make populate-secrets` which reads from `backend/.env.local`. This keeps
plaintext credentials out of Pulumi state and git history.

Exception: `DATABASE_URL` is constructed by Pulumi after Cloud SQL is created
(private IP only known at runtime) and written as a `SecretVersion` automatically.
`make populate-secrets` must never overwrite this — see below.

### DATABASE_URL ownership boundary — Pulumi owns it, not .env.local
`DATABASE_URL` in Secret Manager is constructed and written by Pulumi from:
- Cloud SQL's private IP (`instance.private_ip_address` output)
- The generated DB password (`pulumi_random.RandomPassword`)

This value should never be manually managed. The risk: if `DATABASE_URL` appears
in the `# --- secrets ---` section of `.env.local` (pointing at local Postgres),
running `make populate-secrets` will overwrite the Cloud SQL URL with the local
one — breaking Cloud Run on the next cold start.

**Rule:** `DATABASE_URL` belongs in the `# --- variables ---` section of `.env.local`
so the populate script ignores it. Cloud Run reads the Cloud SQL URL from Secret
Manager via the Pulumi-managed `SecretVersion`. Local dev reads the local Postgres
URL from `.env.local` via `load_dotenv`.

```bash
# .env.local — correct structure
# --- secrets ---
ANTHROPIC_API_KEY=...      ← managed by populate-secrets.sh
OPENAI_API_KEY=...
FAL_API_KEY=...
# DATABASE_URL is managed by Pulumi — never put it here

# --- variables ---
DATABASE_URL=postgresql+psycopg://postgres:123456@localhost:5432/mydb  ← local only
GCP_PROJECT_ID=shared-apps-infrastructure
GCP_REGION=europe-west2
GCP_STORAGE_BUCKET=storyengine-dev-media-x7k2
GOOGLE_APPLICATION_CREDENTIALS=...
```

### .env.local uses section markers to separate secrets from plain vars
The `populate-secrets.sh` script reads the file line by line, tracking which
section it's in. Only keys under `# --- secrets ---` are uploaded to Secret
Manager. Everything under `# --- variables ---` is ignored by the script —
those values are either local-only (like `DATABASE_URL`) or injected directly
as plain env vars in the Cloud Run service definition (like `GCP_PROJECT_ID`).

### load_dotenv uses override=False
`core/config.py` loads `.env.local` with `override=False`, meaning explicit
environment variables set by the shell take precedence over the file. This allows
tools like `make migrate` to inject a specific `DATABASE_URL` without being
stomped by the local file. Normal dev usage is unaffected — the shell has no
conflicting env vars set.

---

## Layer 5 — Cloud Run

### Direct VPC Egress, not VPC Connector
Cloud Run Direct VPC Egress attaches containers directly to the subnet network
interface. VPC Connector (the legacy approach) required a managed cluster of
proxy VMs in the subnet. Direct Egress is simpler, cheaper, and recommended
for new deployments.

### egress=PRIVATE_RANGES_ONLY
Only RFC 1918 private IP traffic routes through the VPC (reaching Cloud SQL at
`10.1.0.3`). Public internet traffic and Google API calls (GCS, Secret Manager,
Artifact Registry) go direct via `private_ip_google_access` on the subnet.
More efficient than `ALL_TRAFFIC` and avoids unnecessary VPC routing for
Google API calls.

### Memory limit: 1Gi
Cloud Run defaults to 256MB. The Python runtime + grpcio + pillow + sqlalchemy
exceed 512MB at startup. 1Gi gives comfortable headroom for dev. Revisit for
prod based on actual observed memory usage.

### Dockerfile: .venv/bin/uvicorn, not uv run uvicorn
`uv run` checks venv freshness at startup and re-syncs if out of date. Inside a
container this causes it to download 100+ packages before the app starts,
causing OOM and slow cold starts. The venv is correctly built at image build
time — call uvicorn directly from the venv.

### Dockerfile: .dockerignore excludes .venv
Without `.dockerignore`, `COPY . .` copies the local macOS/arm64 `.venv` into
the container, overwriting the correctly-built `linux/amd64` venv from `uv sync`.
The `.venv` directory must be excluded from the build context.

### Health check via Cloud Run startup probe, not Docker HEALTHCHECK
Docker's `HEALTHCHECK` directive is ignored by Cloud Run. The startup probe
is defined in the Cloud Run service definition (in Pulumi) and causes Cloud Run
to hold traffic until `GET /health` returns 200. A failed probe marks the
revision failed and keeps the previous revision live.

---

## Layer 6 — Networking

### CIDR ranges
- Subnet: `10.0.0.0/20` — 4096 addresses for resources in `europe-west2`
- Reserved for Google services: `10.1.0.0/16` — 65536 addresses allocated to
  Google's managed services network via VPC peering. Cloud SQL got `10.1.0.3`.

### private_ip_google_access=True on the subnet
Allows Cloud Run instances (via VPC egress) to reach Google APIs (Secret Manager,
GCS, Artifact Registry) using private Google IP ranges without a NAT gateway.
Without this, Cloud Run would need a Cloud NAT to make outbound API calls.

### servicenetworking.Connection must be created before Cloud SQL
Pulumi doesn't infer this dependency automatically because the connection
resource isn't referenced in the DatabaseInstance arguments. We pass
`peering_connection` explicitly to `create_database()` and declare
`depends_on=[peering_connection]` on the instance. Without this, Pulumi runs
them in parallel and Cloud SQL fails with "network doesn't have at least 1
private services connection".

---

## Layer 7 — Database

### Cloud SQL edition: ENTERPRISE with db-f1-micro
GCP now defaults to ENTERPRISE_PLUS which requires the `db-perf-optimized-N-*`
tier family. ENTERPRISE must be explicitly set to use `db-f1-micro` (~$7/month).
ENTERPRISE_PLUS starts at `db-perf-optimized-N-2` (16GB RAM, ~$400/month).

### DB password generated by Pulumi, stored in Secret Manager
Password is generated via `pulumi_random.RandomPassword` (32 chars, no special
chars to avoid URL-encoding issues). Stored in `storyengine-dev-db-password`
in Secret Manager. Never in git, never in Pulumi config, always retrievable via:
```bash
gcloud secrets versions access latest \
  --secret storyengine-dev-db-password \
  --project shared-apps-infrastructure
```

### ipv4_enabled=True with no authorized networks
Cloud SQL has a public IP but no authorized networks configured, so direct
connections from the internet are rejected. The Auth Proxy uses IAM auth via
TLS tunnel and doesn't require an authorized network entry. Cloud Run uses
the private IP (`10.1.0.3`) via VPC egress. The public IP exists solely to
enable the Auth Proxy for local developer migrations.

### deletion_protection=False in dev
Allows `pulumi destroy` to remove the instance cleanly. Must be set to `True`
in staging and prod — disabling it requires a manual `pulumi up` step before
destroy can proceed, acting as a safety gate.

### Local migrations use Cloud SQL Auth Proxy
The private IP (`10.1.0.3`) is unreachable from developer laptops. The Auth Proxy
opens a local port (`localhost:5433`) that tunnels to Cloud SQL via IAM-authenticated
TLS. `make migrate` reads `DATABASE_URL` from Secret Manager, rewrites the host
to `localhost:5433`, and runs `alembic upgrade head` directly via `.venv/bin/alembic`.

CI migrations use the Cloud Run Job instead — see Layer 9.

---

## Layer 8 — Frontend Hosting

### Bucket name must match the domain
GCP requires the GCS bucket name to exactly equal the domain being served when
using a load balancer backend bucket. `dev.dekatha.com` → bucket named
`dev.dekatha.com`. Changing the subdomain requires creating a new bucket,
syncing files, updating the LB backend, then deleting the old bucket.

### Load balancer is required for custom domain + HTTPS
GCS cannot serve HTTPS on a custom domain directly. The chain is:
`Global Forwarding Rule → Target HTTPS Proxy (SSL termination) → URL Map →
Backend Bucket → GCS`. The load balancer holds the managed SSL certificate
and binds the static IP. HTTP (port 80) uses a separate forwarding rule that
returns a 301 redirect to HTTPS via a redirect URL map.

### Google-managed SSL certificate provisioning requires DNS first
The cert stays in `PROVISIONING` or `FAILED_NOT_VISIBLE` until the domain's
A record resolves to the load balancer IP. Do not expect the cert to provision
until DNS propagates. `FAILED_NOT_VISIBLE` is not permanent — GCP retries
automatically once DNS is correct.

### Cloudflare proxy must be disabled (grey cloud) for GCP-managed certs
Cloudflare's proxied mode intercepts TLS before it reaches GCP, preventing
the managed certificate from provisioning. Set the A record to DNS-only mode
in Cloudflare. CDN/DDoS protection via Cloudflare can be re-enabled later
once the cert is active, at the cost of losing GCP's managed cert (Cloudflare
would handle TLS instead).

### Vite env files control the backend URL baked into the JS bundle
Vite replaces `import.meta.env.VITE_*` at build time — the value is a literal
string in the output bundle, not a runtime env var. Environment-specific values:
- `.env.development` — loaded by `npm run dev`, points at `localhost:8085`
- `.env.production` — loaded by `npm run build`, does NOT set `VITE_BACKEND_URL`

`VITE_BACKEND_URL` is intentionally absent from `.env.production`. It is injected
at build time from the live stack output (`pulumi stack output service_url`) by
both `make deploy-frontend` and the CI/CD pipeline. This guarantees it always
matches the live infrastructure — hardcoding it in `.env.production` would produce
stale URLs silently whenever the Cloud Run service URL changes.

`constants.ts` is unchanged — it reads `import.meta.env.VITE_BACKEND_URL` with
a fallback, which is always set correctly at build time via the above mechanism.

### FRONTEND_URL is the canonical frontend origin in infra
For the auth rollout, infra standardizes on a single plain env var:
`FRONTEND_URL=https://dev.dekatha.com`. This value is used for frontend
redirect destinations and browser CORS policy in the backend.

The canonical external backend origin is provided separately as:
`API_URL=https://api.dekatha.com`. OAuth callback URLs are built from this
value so Google always sees the public HTTPS API origin rather than an
internally reconstructed request URL after load balancer TLS termination.

Local dev must provide both settings in `backend/.env.local`, keeping the
frontend and backend public origins explicit across environments.

---

## Layer 9 — Migration Job (Cloud Run Job)

### Cloud Run Job instead of Auth Proxy in CI
GitHub Actions runners are outside the VPC. Cloud SQL has a private IP only —
there is no path from a runner to `10.1.0.3` without a tunnel. The alternatives:

- **Cloud SQL Auth Proxy in CI** — requires downloading the proxy binary,
  authenticating it, and running it as a background process. Fragile, adds
  latency, and exposes the database port on the runner.
- **Cloud Run Job** — runs `alembic upgrade head` inside the VPC using direct
  VPC egress. CI just calls `gcloud run jobs execute ... --wait` and reads the
  exit code. The runner never touches the database directly.

The Cloud Run Job is simpler, more secure, and uses the same network path as the
running application.

### Same image as the Cloud Run service
The migration job uses the same Docker image as the backend service, tagged with
the same git SHA. This guarantees that migration files in the image match the
application code deployed in the same `pulumi up`. Running migrations with the
old image before `pulumi up` would miss any migration files added in the current
commit.

### max_retries=0
A failed migration must not retry automatically. If `alembic upgrade head` fails
mid-way, the schema is in a partially-applied state. Retrying blindly can make
this worse. The job exits non-zero, CI halts, and a human investigates. Recovery
is manual: fix the migration, push a new commit.

### Step ordering in CI: pulumi up before migrate
`pulumi up` updates both the Cloud Run service and the migration job to the new
image tag. The migration job must be on the new image before it runs — otherwise
it executes the old image's migration files and misses anything added in the
current commit.

---

## Layer 10 — CI/CD (GitHub Actions)

### Two-workflow split
- `ci.yml` — runs on every pull request push. Lint + type-check + build only.
  Fast feedback during code review. Does not deploy anything.
- `deploy.yml` — runs on push to `main` only (i.e. merged PRs). Inlines its own
  CI gate jobs, then deploys if both pass.

`ci.yml` does not run on push to `main` — `deploy.yml` owns that event entirely.
Running both on `main` would duplicate the CI jobs on every merge with no benefit.

### deploy.yml inlines CI rather than reusing ci.yml
GitHub's `uses:` syntax for reusing workflows requires the called workflow to
declare `on: workflow_call`. `ci.yml` does not declare this (and should not be
modified). The deploy workflow inlines identical CI jobs and gates the deploy job
on both with `needs: [ci-backend, ci-frontend]`.

### Workload Identity Federation — no JSON key file
GitHub Actions authenticates to GCP via OIDC, not a JSON key:

1. GitHub generates a short-lived OIDC token for the workflow run.
2. The GCP Workload Identity Pool exchanges it for a temporary GCP access token
   scoped to `github-actions-sa`.
3. The token expires when the workflow ends.

The pool's `attribute_condition` rejects tokens from any repo other than
`anudeep22003/organism`. A leaked token from a different repo cannot impersonate
`github-actions-sa`. Nothing to rotate, nothing to leak.

### github-actions-sa uses roles/editor at project level
Pulumi manages Cloud Run, Cloud SQL, Secret Manager, VPC, GCS, Artifact Registry,
IAM bindings, and more. The exhaustive list of individual roles required is 20+
and changes whenever a new resource type is added to the stack. `roles/editor`
at project level covers all of it in one binding.

`roles/editor` does not include IAM permissions (`roles/iam.*`) — this is
intentional. `github-actions-sa` can manage resources but cannot grant itself
or others new IAM roles.

### State bucket IAM is not explicitly bound
The Pulumi state bucket (`storyengine-infra-state`) was created manually before
the Pulumi stack existed — it is not managed by Pulumi. Attempting to bind IAM
on it via `gcp.storage.BucketIAMMember` fails with a 404 because the Pulumi
provider cannot find the bucket in its own state.

`roles/editor` at project level includes `storage.objectAdmin` on all buckets in
the project, including the state bucket. No separate binding is needed.

### Python and Node versions are pinned via version files
- `infra/.python-version` — pins Python 3.12 for the Pulumi runtime. Read by
  `uv python install` in CI.
- `backend/.python-version` — pins Python 3.12 for the backend. Same mechanism.
- `frontend/.nvmrc` — pins Node 22 for the frontend build. Read by
  `actions/setup-node` via `node-version-file: frontend/.nvmrc`.

Pinning prevents CI from silently upgrading to a newer runtime when new versions
are released, which could introduce subtle incompatibilities.

### Deploy step ordering
1. `docker build + push` — image must exist in Artifact Registry before Pulumi
   references it in the Cloud Run service definition.
2. `pulumi up` — updates Cloud Run service and migration job to the new image tag.
3. `gcloud run jobs execute ... --wait` — runs migrations with the new image.
   Must happen after `pulumi up` so the job has the new image. Must happen before
   traffic shifts to the new revision (Cloud Run shifts traffic as part of
   `pulumi up`, but the startup probe holds traffic until `/health` returns 200,
   giving migrations time to complete).
4. `pulumi stack output service_url` → `VITE_BACKEND_URL` — frontend build
   injects the live backend URL. Must happen after `pulumi up` so the URL is
   current.
5. `npm run build + gcloud storage rsync` — frontend last, no dependency on
   backend revision being healthy.

---

## Operational Notes

### Loguru Cloud Run JSON logging — use callable sink, not format=
Loguru's `format=` callable receives a record and its return value is used as a
**format string template** — Loguru then calls `.format_map()` on it. A JSON
string like `{"severity": "INFO"}` breaks `format_map` because `"severity"` with
quotes is not a valid Python format key (`KeyError: '"severity"'`).

Fix: pass the formatter as the **sink** (first positional arg to `logger.add()`).
When the sink is callable, Loguru passes the message object directly and the
callable writes to `sys.stdout` — `format_map` is never called.

Also: `diagnose=False` in production — `diagnose=True` includes local variable
values in tracebacks, which can leak sensitive data (tokens, request bodies) into
Cloud Logging.

---

## What's Next

Planned work not yet built:

- **Staging environment** — duplicate the stack with `pulumi stack init staging`
- **Cloud SQL HA** — flip `availability_type=REGIONAL` and `deletion_protection=True` for prod
- **IAM database auth** — replace password auth with `cloudrun-sa` identity as Postgres user
- **Redis / Memorystore** — same private services access pattern as Cloud SQL
