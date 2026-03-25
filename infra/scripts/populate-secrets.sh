#!/usr/bin/env bash
# populate-secrets.sh
#
# Reads the project .env.local file and uploads values from the
# "# --- secrets ---" section to GCP Secret Manager.
#
# Only keys in the secrets section are uploaded. Keys in the
# "# --- variables ---" section (plain env vars) are ignored —
# those are injected directly into Cloud Run as plain env vars.
#
# The script is IDEMPOTENT: it compares the current active version
# in Secret Manager against the local value and only creates a new
# version if the value has changed. Safe to run any time.
#
# Usage:
#   bash infra/scripts/populate-secrets.sh
#
# Prerequisites:
#   - gcloud authenticated (gcloud auth login)
#   - .env.local structured with section comments:
#       # --- secrets ---
#       ANTHROPIC_API_KEY=...
#       # --- variables ---
#       GCP_PROJECT_ID=...

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT="shared-apps-infrastructure"
SECRET_PREFIX="storyengine-dev"

# Path to the env file — relative to the repo root.
# Script can be run from anywhere in the repo.
REPO_ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="${REPO_ROOT}/backend/.env.local"

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: env file not found at $ENV_FILE" >&2
  exit 1
fi

if ! grep -q "# --- secrets ---" "$ENV_FILE"; then
  echo "ERROR: $ENV_FILE has no '# --- secrets ---' section marker." >&2
  echo "Add '# --- secrets ---' above your secret keys and" >&2
  echo "'# --- variables ---' above your plain env vars." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Parse and upload
# ---------------------------------------------------------------------------

in_secrets_section=false
uploaded=0
skipped=0
errors=0

echo "Reading secrets from: $ENV_FILE"
echo "Uploading to project:  $PROJECT"
echo ""

while IFS= read -r line; do
  # Section markers — flip state
  if [[ "$line" == "# --- secrets ---" ]]; then
    in_secrets_section=true
    continue
  fi
  if [[ "$line" == "# --- variables ---" ]]; then
    in_secrets_section=false
    continue
  fi

  # Only process lines in the secrets section
  if [[ "$in_secrets_section" != true ]]; then
    continue
  fi

  # Skip blank lines and comment lines
  if [[ -z "$line" || "$line" =~ ^# ]]; then
    continue
  fi

  # Parse KEY=VALUE — value may contain = signs (e.g. base64, URLs)
  if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
  else
    echo "  WARN: skipping unparseable line: $line" >&2
    continue
  fi

  # GCP secret name: prefix + lowercase key with underscores → hyphens
  # e.g. ANTHROPIC_API_KEY → storyengine-dev-anthropic-api-key
  # Uses tr for lowercasing — compatible with macOS bash 3.2
  secret_name="${SECRET_PREFIX}-$(echo "$key" | tr '[:upper:]' '[:lower:]' | tr '_' '-')"

  # Check current active version (may not exist yet on first run)
  current_value=$(gcloud secrets versions access latest \
    --secret="$secret_name" \
    --project="$PROJECT" 2>/dev/null || echo "__NOT_SET__")

  if [[ "$current_value" == "$value" ]]; then
    echo "  SKIP  $key  (value unchanged)"
    ((skipped++)) || true
  else
    if [[ "$current_value" == "__NOT_SET__" ]]; then
      echo "  ADD   $key  (first version)"
    else
      echo "  ADD   $key  (value changed — creating new version)"
    fi

    if echo -n "$value" | gcloud secrets versions add "$secret_name" \
        --data-file=- \
        --project="$PROJECT" 2>/dev/null; then
      ((uploaded++)) || true
    else
      echo "  ERROR $key  (failed to upload — does the secret container exist? Run pulumi up first)" >&2
      ((errors++)) || true
    fi
  fi

done < "$ENV_FILE"

echo ""
echo "Done. uploaded=$uploaded  skipped=$skipped  errors=$errors"

if [[ "$errors" -gt 0 ]]; then
  echo ""
  echo "Some secrets failed to upload. Check that 'pulumi up' has been run" >&2
  echo "to create the secret containers before running this script." >&2
  exit 1
fi
