# Handoff: Config Refactor + Cloud Run Migration Job

## What We Were Actually Doing

We were setting up a **Cloud Run Job to run Alembic migrations** as part of building
toward a full CI/CD pipeline. The current `make migrate` uses the Cloud SQL Auth Proxy
(a tunnel from a developer laptop into Cloud SQL). This doesn't work in CI — GitHub
Actions runners have no VPC access. The solution: a Cloud Run Job that runs inside the
VPC and reaches Cloud SQL's private IP directly.

The Cloud Run Job (`storyengine-dev-migrate`) has already been created via Pulumi and
is defined in `infra/components/migrations.py`. The Makefile targets (`make migrate`,
`make migrate-down`, `make migrate-status`, `make migrate-history`) have been updated
accordingly. That work is committed and deployed.

**The job kept failing** because `alembic/env.py` imports app models for autogenerate
support, those models transitively import `core.services.database`, which imports
`core.config`, which validates ALL required env vars (API keys, GCP vars) at import
time. The migration job only has `DATABASE_URL` — it doesn't need API keys to run
migrations. This triggered an exception before alembic could even connect.

We attempted a workaround (placeholder env vars in `env.py`) which was brittle, then
undertook a proper refactor.

---

## What Was Attempted (Now Stashed)

A full migration to `pydantic-settings` is in `stash@{0}` on branch `infra/set-up`.
The stash contains partial work including:

- `pydantic-settings` added to `pyproject.toml` (already in `uv.lock`)
- `core/config.py` rewritten with `DatabaseSettings` + `AppSettings` classes
- `core/services/database.py` made lazy (engine created on first call via `lru_cache`)
- `core/auth/__init__.py` cleaned up (FastAPI route dependencies removed from exports)
- `alembic/env.py` partially rewritten
- Various usage sites updated from `from core.config import X` to `get_settings().x`

**The stash should not be applied directly** — the approach was refined mid-execution
and the stash contains a half-migrated inconsistent state. Start fresh with the plan
below.

---

## The Correct Implementation Plan

### Structure

Convert `core/config.py` (single file) into a module:

```
backend/core/config/
    __init__.py     ← imports only from app.py (not database.py)
    database.py     ← DatabaseSettings class only, no instantiation
    app.py          ← AppSettings(DatabaseSettings) + settings = AppSettings()
```

### Why This Works

The root problem: any `from core.config import X` executes the entire `core/config.py`
module, including `settings = AppSettings()`, which fails without API keys.

By splitting into a module:

- `alembic/env.py` does `from core.config.database import DatabaseSettings` — this
  imports only `database.py`, never touches `app.py`, so `AppSettings()` never runs.
- All app code does `from core.config import settings` — this imports `core/config/__init__.py`,
  which imports from `app.py`, which runs `settings = AppSettings()` as a module-level
  singleton. Correct.
- No circular reference: `database.py` imports nothing from `core.config`. `app.py`
  imports from `core.config.database` (direct file import, bypasses `__init__.py`).
  `__init__.py` imports from `app.py`.

### File Contents

**`core/config/database.py`:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Minimal settings for alembic migrations — only DATABASE_URL required."""

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_ignore_empty=True,
        extra="ignore",
    )
```

**`core/config/app.py`:**
```python
from pydantic_settings import SettingsConfigDict

from core.config.database import DatabaseSettings


class AppSettings(DatabaseSettings):
    """Full application settings. Instantiated once as a module-level singleton."""

    openai_api_key: str
    anthropic_api_key: str
    fal_api_key: str
    gcp_project_id: str
    gcp_region: str
    gcp_storage_bucket: str
    google_application_credentials: str = ""  # optional, localhost only

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = AppSettings()  # type: ignore[call-arg]
```

**`core/config/__init__.py`:**
```python
from core.config.app import AppSettings, settings

__all__ = ["AppSettings", "settings"]
```

Note: `DatabaseSettings` is intentionally NOT re-exported from `__init__.py`.
Only `alembic/env.py` needs it, and it imports directly from `core.config.database`.
This is what prevents `app.py` from executing when alembic runs.

### Changes Needed

**Delete** `core/config.py`.

**Create** `core/config/` as above (3 files).

**Change `alembic/env.py`** — one line:
```python
# before:
from core.config import DatabaseSettings

# after:
from core.config.database import DatabaseSettings
```

Everything else stays the same. All `from core.config import settings` imports across
the codebase continue to work without modification.

### Usage Sites That Stay Unchanged

These files import `from core.config import settings` or individual vars and require
**no changes** after the module split:

- `backend/main.py`
- `backend/core/services/database.py`
- `backend/core/services/intelligence/clients.py`
- `backend/core/services/intelligence/media_generator.py`
- `backend/core/storage/google.py`
- `backend/core/story_engine/service/image_service.py`
- `backend/tests/conftest.py`
- `backend/tests/story_engine/test_image_upload_service.py`

**Wait — these files currently import old bare-variable names** (e.g.
`from core.config import OPENAI_API_KEY`). The stash changed them to `get_settings()`
which was then stashed. The current committed state (`f1be102`) has `pydantic-settings`
but the usage sites in the stash are half-migrated.

**Check the actual current state of each file before editing.** Run:
```bash
grep -rn "from core.config import" backend --include="*.py" | grep -v .venv
```

The expected current state after `f1be102` is that usage sites still reference bare
vars (`OPENAI_API_KEY` etc.) since the stash reverted them. The module split will make
those bare vars unavailable — you need to update them to `settings.openai_api_key` etc.

### Full File Change Inventory

| File | What to do |
|------|-----------|
| `backend/core/config.py` | Delete |
| `backend/core/config/__init__.py` | Create — imports from `app.py` only |
| `backend/core/config/database.py` | Create — `DatabaseSettings` class |
| `backend/core/config/app.py` | Create — `AppSettings` + `settings = AppSettings()` |
| `backend/alembic/env.py` | Change import to `from core.config.database import DatabaseSettings` |
| `backend/core/services/database.py` | `from core.config import settings` + `settings.database_url` |
| `backend/core/services/intelligence/clients.py` | `settings.openai_api_key` |
| `backend/core/services/intelligence/media_generator.py` | `settings.fal_api_key` |
| `backend/core/storage/google.py` | `settings.gcp_storage_bucket` |
| `backend/core/story_engine/service/image_service.py` | `settings.gcp_project_id`, `settings.gcp_storage_bucket` |
| `backend/main.py` | Remove `from core import config  # noqa: F401` hack, use `from core.config import settings` (used explicitly in lifespan log) |
| `backend/tests/conftest.py` | `settings.database_url` |
| `backend/tests/story_engine/test_image_upload_service.py` | `settings.gcp_project_id`, `settings.gcp_storage_bucket` |

Also check for any file still exporting `get_current_user_id` from `core.auth`:
```bash
grep -rn "from core.auth import get_current_user_id" backend --include="*.py" | grep -v .venv
```
The stash removed this from `core/auth/__init__.py` and updated 4 route files
(`phases.py`, `v2/images.py`, `v2/character.py`, `v2/story.py`) to import from
`core.auth.dependencies` instead. This change is clean and correct — keep it.

---

## Other Structural Changes That Should Also Be Applied

These were in the stash and are correct regardless of the config approach:

### `core/auth/__init__.py`
Remove `get_current_user_id` and `get_user_manager` from exports. These are FastAPI
route dependencies, not package-level API. Their presence in `__init__.py` creates the
import chain that pulls `core.services.database` into `alembic/env.py`.

```python
# Remove this line:
from .dependencies import get_current_user_id, get_user_manager
# And remove them from __all__
```

Four route files need updating to import directly:
```python
# before:
from core.auth import get_current_user_id
# after:
from core.auth.dependencies import get_current_user_id
```
Files: `api/phases.py`, `api/v2/images.py`, `api/v2/character.py`, `api/v2/story.py`

### `core/services/database.py`
Make engine creation lazy — currently creates a live engine at module import time:

```python
# Current (bad — side effect on import):
async_db_engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(bind=async_db_engine)

# Fix:
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_session_maker() -> "async_sessionmaker[AsyncSession]":
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(bind=engine)

async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _get_session_maker()() as session:
        yield session
```

The `get_async_db_session` signature is unchanged — all `Depends(get_async_db_session)`
usage sites are unaffected. `async_session_maker` as a module-level export goes away.

One file uses it directly: `core/sockets/handlers.py`. Change:
```python
# before:
from core.services.database import async_session_maker
async with async_session_maker() as async_db_session:

# after:
from core.services.database import get_async_db_session
async for async_db_session in get_async_db_session():
```
After this change, add `session = None` initialisation alongside `target_room = None`
to fix a mypy "possibly unbound" error on the `session` variable used after the loop.

---

## Verification Steps

After all changes:

```bash
# 1. Lint and type check
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .

# 2. Build and deploy
cd infra && make deploy-backend

# 3. Run the migration job — this is the whole point
make migrate
```

Expected migration output in Cloud Logging:
```
INFO [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO [alembic.runtime.migration] Will assume transactional DDL.
INFO [alembic.runtime.migration] Running upgrade ... (or "No migrations to apply")
```

Also test the downgrade path:
```bash
make migrate-down && make migrate
```

---

## Current Committed State

Branch: `infra/set-up`
HEAD: `f1be102 refactor(config): migrate to pydantic-settings with DatabaseSettings/AppSettings`

At `f1be102`, `pydantic-settings` is in `pyproject.toml` and `uv.lock`. The
`core/config.py` file has `DatabaseSettings` and `AppSettings` classes but also a
`get_settings()` function and NO module-level `settings` singleton (the singleton
was removed mid-session). Usage sites are in inconsistent state — some import bare
vars (`OPENAI_API_KEY`), some import `get_settings()`, some import `settings`.

The stash (`stash@{0}`) has the half-migrated work but should not be applied.
**Start fresh from `f1be102`** and implement the module split as described above.

---

## Infra Context

The Cloud Run Job is already provisioned. `make migrate` triggers it. The job:
- Runs the same backend image (same git SHA as the service)
- Overrides CMD to `.venv/bin/alembic upgrade head`
- Runs inside the VPC (same subnet as the service)
- Reads `DATABASE_URL` from Secret Manager via `cloudrun-sa`
- `max_retries=0` — fails fast, no retry on partial migration

Once the config refactor is done and `make migrate` works, the next step is CI/CD:
GitHub Actions workflow that builds → pushes image → runs `pulumi up` → runs `make
migrate` (via `gcloud run jobs execute --wait`) on every push to `dev` or `main`.
