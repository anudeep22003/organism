# Agent Context — `core/auth`

This module is the backend auth system.

Treat it as the long-term auth home, not as a temporary experiment.

## Philosophy

Build the simplest thing that works, but keep the boundaries clean enough that the next step stays obvious.

The design principles here are:
- thin HTTP layer
- service-owned orchestration
- repository-owned persistence only
- security concerns isolated under `security/`
- provider-specific modeling where the provider payload or lifecycle genuinely differs

Do not collapse layers just because the module is still small. The current structure is deliberate.

## Package Shape

The package is organized into these areas:
- `api/`
  - HTTP-only concerns
  - router, cookies, CSRF middleware, dependencies, OAuth client wiring
- `services/`
  - orchestration and transaction ownership
  - this is where auth flows are coordinated
- `repositories/`
  - database reads/writes only
  - repositories do not commit
- `models/`
  - ORM entities and entity-local factory/update methods
- `security/`
  - token managers, hashers, encryption, rate limiting
- package root
  - minimal cross-boundary exports

Keep new code in the right layer. Do not put orchestration in the router or persistence logic in services.

## How To Read This File

This document mixes three kinds of guidance:
- stable invariants
  - boundaries that are part of the current architecture and should usually stay in place
- current defaults
  - decisions we made because they were the best fit with today’s knowledge
- user-confirmation changes
  - places where a future agent should pause before making a foundational shift

The goal is not to freeze the design forever. The goal is to preserve the reasoning behind today’s decisions so future work improves the system instead of accidentally undoing it.

## Naming Rules

Inside this package, do not introduce new `v2` suffixes.

Reason:
- this package is now the canonical `auth` package
- internal names should read like the final system, not a migration phase

Good:
- `AuthService`
- `AuthRepository`
- `get_current_user_id`

Avoid:
- `AuthServiceV2`
- `get_current_user_id_v2`
- `auth_*_v2`

## Import Rules

Within `core/auth`, prefer relative imports for module-local code.

Example:
- import auth-local helpers via `from ..security import ...` or `from .cookies import ...`

Shared infrastructure can stay explicit:
- `core.common`
- `core.services.database`
- `core.config`

Do not create flat compatibility shim files just to re-export moved modules. If a symbol needs to cross the package boundary, export it from `core/auth/__init__.py`.

## Public Backend Contract

The current auth surface is:
- `GET /api/auth/login`
- `GET /api/auth/callback`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

Important behavior:
- `login` is a browser redirect starter, not a JSON endpoint
- `callback` handles Google OAuth, persists/link users, issues our local session cookies, and redirects to the frontend
- `refresh` returns `204 No Content`
- `logout` returns `204 No Content`
- `me` is the authoritative “current user” endpoint

Current default:
- keep this module cookie-first and keep `refresh` as `204 No Content`

Reason:
- this keeps browser auth simpler
- it reduces token exposure in frontend JS
- it aligns the backend contract around cookies plus `/me`

If changing this would materially improve the overall system, confirm it with the user first because it affects frontend architecture, CSRF posture, and socket auth.

## Session Model

This module uses our own app session system on top of Google login bootstrap.

Key decisions:
- access token is a JWT cookie
- refresh token is an opaque DB-backed cookie
- refresh tokens are rotated
- logout revokes the local session and clears cookies
- our app session lifecycle is separate from Google token lifecycle

The existing `session` table is the current home for our app refresh/session state.

Current default:
- keep local AT/RT/session state out of `user`

Reason:
- `user` is the canonical local identity row
- session state already has a better home in `session`

If a future design would benefit from changing that, discuss it with the user first rather than drifting there piecemeal.

## Cookie And CSRF Model

Current cookie posture:
- `access_token`
  - HttpOnly
  - path `/`
- `refresh_token`
  - HttpOnly
  - path `/api/auth`
- `csrf_token`
  - readable by JS
  - path `/`

CSRF uses the double-submit cookie pattern:
- frontend reads `csrf_token`
- frontend sends it in `X-CSRF-Token`
- middleware compares cookie and header on unsafe requests

Important:
- `GET /api/auth/callback` is not protected by this middleware; OAuth state/nonce covers that flow
- the middleware currently bypasses requests that do not carry the `csrf_token` cookie so legacy auth is not broken during migration
- once legacy auth is removed, that bypass should be revisited and likely deleted

## Security Decisions

These are the current security defaults:

- access tokens are signed JWTs
- refresh token secrets are hashed with Argon2
- refresh token lookup uses `session_id.secret`, not “hash and query by hash”
- stored Google tokens are encrypted on write
- production encryption uses Fernet
- non-production currently uses `LocalOnlyNonEncryptor` as a pass-through for local/dev convenience

Reason:
- these choices separate lookup from secret verification cleanly
- they avoid deterministic plain-hash refresh-token patterns
- they keep provider credentials out of plaintext storage in production
- they keep the frontend from depending on readable auth credentials

If changing any of these would improve the overall system, confirm the tradeoff with the user first because it affects rollout, security posture, and frontend behavior.

If you add new encrypted fields, follow the current `TokenEncryptor` boundary and keep encryption out of repositories.

## Data Modeling Rules

### Local user identity

`user` remains the canonical local app identity row.

Current default:
- keep provider-specific credential fields out of `user`

Reason:
- provider credential lifecycle is different from local user identity
- mixing them makes both the schema and the auth flow harder to reason about

If changing that would simplify the overall system without blurring those concerns, discuss it with the user first.

### Google linkage

Google is modeled with a provider-specific table:
- `google_oauth_account`

That is intentional.

Reason:
- provider payloads and lifecycle differ
- we do not want to prematurely force all providers into a generic OAuth table

Current default:
- if a new provider’s shape genuinely differs, start with another provider-specific table

Reason:
- Google already proved that provider payloads and lifecycle are not generic by default

If a shared provider abstraction would clearly improve the system, confirm that with the user before widening the model.

### Multiple linked accounts

One local `user` may have multiple linked Google accounts.

Current relationship shape:
- `User.google_oauth_accounts`
- `GoogleOAuthAccount.user`

Keep that flexibility unless product requirements change.

### Re-login behavior

On successful Google login:
- find existing account by provider subject (`google_sub`)
- update that row in place
- preserve the stored Google refresh token if Google does not resend one
- clear `revoked_at`

Current default:
- update provider state in place on relogin instead of creating a new row each time

Reason:
- this table models current provider state, not a login event log

If the product later needs login history or auditability, add that explicitly rather than overloading the provider credential table.

## Future Provider Guidance

If you add another login provider:
- do not reuse the Google table for it
- start with:
  - provider-specific model
  - provider-specific repository if needed
  - service flow that mirrors the current Google pattern

Current default:
- wait until at least two providers prove the abstraction before extracting a shared provider layer

Reason:
- we chose provider-specific modeling because it kept the current system honest and easy to extend

If a generic provider abstraction would materially improve the system, confirm that move with the user first.

## Service And Repository Rules

Services:
- own orchestration
- own transaction boundaries
- may construct models using model factory/update methods
- may coordinate multiple repositories

Repositories:
- perform persistence only
- do not commit
- do not contain business logic
- accept model instances or narrow persistence inputs, not “garden list” argument bags

Models:
- may expose entity-local factory/update methods when that improves readability and keeps services thinner

This module intentionally follows the same separation style used in `core/story_engine/api/v2`.

## Error Handling Rules

`core/auth/exceptions.py` is the flat exception surface for this module.

Rules:
- services, repositories, and security code raise typed auth exceptions
- HTTP translation happens in router/dependencies
- do not leak `HTTPException` into services or repositories
- avoid raw `ValueError` for auth domain failures

The callback intentionally collapses known auth/provider failures into the same frontend failure redirect. Keep richer detail in logs, not in redirect query params, unless the product explicitly needs it.

## Observability Rules

Auth observability is intentionally lightweight.

Use:
- `core/auth/observability.py`
- `log_auth_event(...)`

Current event families include:
- `auth.login.started`
- `auth.login.succeeded`
- `auth.login.failed`
- `auth.oauth.callback.failed`
- `auth.refresh.succeeded`
- `auth.refresh.failed`
- `auth.logout.succeeded`
- `auth.rate_limited`

Rules:
- log at the auth boundary, not in low-level helpers
- never log tokens, cookie values, or raw OAuth payloads
- do log safe identifiers and outcome metadata:
  - `user_id`
  - `google_sub`
  - `route`
  - `ip`
  - `user_agent`
  - failure reason class

Current default:
- keep observability lightweight and log-based

Reason:
- that was the right fit for the current operational maturity

If adding metrics, tracing, or audit persistence would materially improve the system, discuss that with the user before broadening the observability surface.

## Rate Limiting

The current rate limiter is intentionally simple:
- in-memory
- per-instance
- per-IP
- auth-only

Current limited routes:
- `GET /api/auth/login`
- `GET /api/auth/callback`
- `POST /api/auth/refresh`

`logout` is intentionally not throttled.

Treat the current limiter as immediate app-layer protection, not a final distributed solution.

Current default:
- keep the in-memory limiter simple

Reason:
- it gives immediate auth hardening without new infrastructure

If stronger production-wide enforcement would improve the system, confirm with the user before moving to a shared-store or infra-level model.

## Frontend Contract Assumptions

This module currently assumes the frontend will move to cookie auth.

Important implications:
- frontend should not read access tokens
- frontend should use `/api/auth/me` as the source of truth
- frontend should treat `refresh` as a cookie rotation endpoint returning `204`
- frontend must send the CSRF header on unsafe requests

There is a frontend handoff note in `.notes/auth-frontend-handoff.md` that documents the current expected cutover.

## Infra Assumptions

This module expects infra to provide:
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `JWT_SECRET_KEY`
- `AUTH_SESSION_SECRET`
- `FERNET_ENCRYPTION_KEY`
- `FRONTEND_URL`
- `API_URL`

There is an infra handoff note in `.notes/auth-infra-handoff.md`.

Important deployment assumptions:
- Google OAuth authorized redirect URI must be `${API_URL}/api/auth/callback`
- cookie auth currently assumes same-site frontend/backend deployment characteristics because cookies use `SameSite=Lax`

## Testing Guidance

Relevant test files today:
- `tests/test_auth_api.py`
- `tests/test_auth_tokens.py`
- `tests/test_auth_repository.py`

Keep tests focused and layered:
- API tests for HTTP contract and cookie behavior
- repository tests for persistence behavior
- targeted lower-level tests for token/encryption behavior

Be careful with tests that create committed rows outside shared fixtures. If a test creates rows through the real callback flow, make sure cleanup is failure-safe.

## Stable Invariants

These are the parts of the current architecture that should usually stay in place unless the user explicitly wants a broader redesign:
- keep the router thin
- keep transaction ownership in services
- keep repositories commit-free
- keep HTTP translation out of services and repositories
- keep `/api/auth/me` as the authoritative current-user endpoint
- keep `refresh` and `logout` as session-management endpoints, not identity bootstrap endpoints

## Current Defaults

These are current design defaults, not eternal truths:
- cookie-first auth instead of frontend-readable bearer tokens
- provider-specific modeling instead of a generic OAuth abstraction
- Argon2 for refresh-token secret hashing
- Fernet-backed reversible encryption in production
- lightweight log-based observability
- simple in-memory auth route rate limiting as the first pass

We chose these because they were the best fit for the current system shape, rollout stage, and shared level of knowledge at the time.

## Changes That Need User Confirmation

Before making these kinds of shifts, ask whether they would improve the overall system and confirm with the user:
- changing the cookie-first auth transport model
- reintroducing frontend-readable access tokens
- moving persistence logic into routers or commit behavior into repositories
- replacing provider-specific modeling with a generic provider abstraction
- changing refresh-token verification to a deterministic plain-hash lookup model
- storing provider tokens unencrypted in production
- changing core auth/session semantics in a way that affects the frontend contract
- introducing new `v2`-style internal names instead of the final intended names

## Likely Next Work

The most likely future changes are:
- adding more identity providers
- cutting the rest of the app over to auth dependencies
- removing legacy auth and renaming this package to `auth`
- redesigning socket auth so it no longer depends on a frontend-readable access token

When making those changes, preserve the current boundaries instead of solving the next problem with special cases.
