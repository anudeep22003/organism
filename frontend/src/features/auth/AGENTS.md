# Auth — Agent Notes

## Purpose

`auth` owns frontend authentication behavior end-to-end.

That includes:

- session bootstrap
- login and logout flow
- auth route guards
- auth callback pages
- redirect handling
- the app-facing auth state exposed through `AuthProvider` / `useAuth`

Transport details live in `src/lib/httpClient.ts`, but auth policy and auth UX live here.

## Current Architecture

Today, the frontend auth flow is cookie-first.

- Session truth comes from `GET /api/auth/me`
- Login is browser navigation to `GET /api/auth/login`
- Refresh is `POST /api/auth/refresh`
- Logout is `POST /api/auth/logout`

Inside this feature:

- `api/` owns endpoint constants, query keys, and query options
- `model/auth.context.tsx` owns the auth state machine
- `routing/` owns protected/guest gating and redirect helpers
- `ui/` owns auth pages and callback UX

The rest of the app should consume auth through the feature public API in `index.ts`, not by reaching into internals.

## Decisions We Took Today

These decisions reflect the current product and backend contract.

- We treat cookies as the auth transport instead of a frontend-readable bearer token.
  - Reason: the backend owns the session, and the frontend should not need to read an access token to function.
- We keep auth as a cohesive app capability with state, guards, and UI in one module.
  - Reason: auth is easier to change safely when the flow is readable in one place.
- We preserve post-login intent through safe internal redirect helpers plus session storage.
  - Reason: the SSO flow leaves the SPA and comes back, so redirect intent needs an explicit roundtrip mechanism.
- We keep query keys and server-state wiring local to the auth module.
  - Reason: auth remains understandable as a single boundary instead of leaking session logic across the app.

These are good defaults, not eternal truths. If a new product need or a clearer architecture suggests a better shape, surface that suggestion to the user.

## Important Constraints

Only a small number of constraints should be treated as hard until the backend contract changes.

- Do not assume JavaScript can read the access token.
- `/api/auth/me` is the frontend bootstrap source of truth for session state.
- Unsafe requests depend on the `csrf_token` cookie and `X-CSRF-Token` header.
- Socket auth is currently disabled because the old JS-token handshake no longer fits the cookie-auth model.

That socket point matters for future work: if realtime auth needs to come back, it should come back through a backend-supported cookie or ticket handshake, not by quietly reintroducing frontend token access.

## How To Evolve This

Future work is allowed to reshape this module when the need is justified.

Examples of acceptable evolution:

- changing provider/query organization
- moving auth to a different top-level bucket if the repo architecture matures
- revisiting callback UX
- revisiting bootstrap or refresh behavior
- re-enabling sockets once the handshake model is redesigned

When suggesting or making those changes, keep these properties intact unless there is a strong reason to change them:

- one clear source of truth for auth state
- one clear boundary between auth policy and transport plumbing
- minimal auth leakage into unrelated features

If a change would materially alter those properties, call it out explicitly to the user instead of treating it as a silent refactor.
