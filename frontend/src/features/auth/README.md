# Auth

`auth` is the active frontend auth runtime.

## Responsibilities

- bootstrap the session from `GET /api/auth/me`
- redirect the browser to `GET /api/auth/login`
- treat cookies as the only source of auth state
- keep route guards and callback handling inside the auth feature
- keep CSRF and refresh behavior centralized in `src/lib/httpClient.ts`

## Public Surface

Import from `src/features/auth/index.ts`.

Primary exports:

- `AuthProvider`, `useAuth`
- `RequireAuth`, `RequireGuest`
- `AuthPage`, `AuthSuccessPage`, `AuthFailurePage`

## Notes

- The frontend does not read an access token from JavaScript.
- Unsafe requests rely on the `csrf_token` cookie and `X-CSRF-Token` header.
- Socket.IO is intentionally disabled until the backend exposes a cookie-compatible handshake.
- `src/lib/httpClient.ts` now assumes cookie auth only; there is no bearer fallback path left in the frontend.
