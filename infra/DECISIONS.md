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

### .env.local uses section markers to separate secrets from plain vars
```
# --- secrets ---       ← populate-secrets.sh uploads these to Secret Manager
ANTHROPIC_API_KEY=...
# --- variables ---     ← injected directly as plain env vars in Cloud Run
GCP_PROJECT_ID=...
```
The script reads the file, uploads only the secrets section, ignores variables.

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

Future: replace with a Cloud Run Job that runs inside the VPC (no proxy needed)
triggered from CI before each deployment.

---

## What's Next

Planned layers not yet built:

- **CI/CD** — GitHub Actions: build image, push, run migrations via Cloud Run Job, deploy
- **Cloud Run Job** — one-shot migration runner inside the VPC, replacing the Auth Proxy pattern
- **Staging environment** — duplicate the stack with `pulumi stack init staging`
- **Cloud SQL HA** — flip `availability_type=REGIONAL` and `deletion_protection=True` for prod
- **IAM database auth** — replace password auth with `cloudrun-sa` identity as Postgres user
- **Redis / Memorystore** — same private services access pattern as Cloud SQL
