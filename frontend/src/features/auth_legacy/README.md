# Auth Feature

This module owns all frontend auth behavior.

## Goals

- Keep auth state in one place (`AuthProvider`).
- Keep HTTP transport concerns in `httpClient`.
- Keep route guards declarative and side-effect light.
- Use TanStack Query with a co-located query key factory.

## Directory Layout

```txt
src/features/auth/
  api/
  model/
  routing/
  session/
  ui/
  index.ts
```

## Core Responsibilities

- `api/`
  - Backend auth API calls (`signin`, `signup`, `me`, `logout`).
  - Query key factory (`authKeys`).
  - Query/mutation hooks and options.
- `model/`
  - `AuthProvider` state machine.
  - `useAuth()` public hook.
- `routing/`
  - `RequireAuth` for protected routes.
  - `RequireGuest` for auth-only routes.
  - Safe redirect parsing/building.
- `session/`
  - Token storage adapter (`token.store`) backed by `httpClient`.
- `ui/`
  - Auth page and form components.

## Auth State Machine

`AuthProvider` exposes:

- `status`: `"checking" | "authenticated" | "unauthenticated"`
- `accessToken`
- `user`
- actions: `signIn`, `signUp`, `signOut`, `refreshSession`

Startup flow:

1. provider initializes with `status="checking"`
2. provider resolves session via `me` query
3. state settles to `authenticated` or `unauthenticated`

## Route Guard Behavior

- `RequireAuth`
  - `checking` -> loading screen
  - `unauthenticated` -> redirects to `/auth?tab=signin&redirect=<requested-path>`
  - `authenticated` -> renders protected outlet
- `RequireGuest`
  - `checking` -> loading screen
  - `authenticated` -> redirects to redirect target or `/`
  - `unauthenticated` -> renders auth outlet

## Query Key Pattern

Keys are defined in `api/auth.query-keys.ts`:

- `authKeys.all = ["auth"]`
- `authKeys.me() = ["auth", "me"]`

Rules:

- Keep keys feature-local.
- Build from generic -> specific.
- Invalidate/update through key factory only.

## HTTP Client Boundary

`src/lib/httpClient.ts` handles:

- auth header injection
- refresh+retry on 401
- refresh de-duplication
- token subscriptions

It must not handle:

- routing decisions
- UI state transitions
- component-level auth policy

## Logout Policy

Frontend always clears local session state even if `/api/auth/logout` fails.

## Extension: Add Firebase / SSO Later

Add provider-specific implementation in `api/` and keep this contract stable:

- `AuthProvider` remains the single source of truth.
- `RequireAuth`/`RequireGuest` remain unchanged.
- Exchange external identity token with backend and continue issuing app session tokens.

## Public Surface

Use imports from `src/features/auth/index.ts` only.

Current exports:

- `AuthProvider`, `useAuth`
- `RequireAuth`, `RequireGuest`
- `AuthPage`
- redirect helpers and auth constants needed by router wiring
