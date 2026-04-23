import {
  AUTH_QUERY_PARAMS,
  AUTH_ROUTES,
} from "../api/auth.constants";

/*
The auth flow has two redirect channels on purpose:

1. Query params are used when we stay inside the SPA and only need to move
   between guarded routes like `/story` -> `/auth?redirect=/story`.
2. Session storage is used for the full SSO roundtrip because the browser
   leaves the SPA for `/api/auth/login` and comes back later on
   `/auth/success`.

Both channels are restricted to safe internal paths so auth never becomes an
open redirect surface.
*/
const POST_AUTH_REDIRECT_STORAGE_KEY = "auth.redirect";

const isSafeInternalRedirect = (
  redirectTarget: string | null | undefined
) => {
  return Boolean(
    redirectTarget &&
      redirectTarget.startsWith("/") &&
      !redirectTarget.startsWith("//")
  );
};

export const getSafeRedirectTarget = (
  redirectTarget: string | null | undefined
) => {
  if (!isSafeInternalRedirect(redirectTarget)) {
    return null;
  }

  return redirectTarget;
};

/*
Build the guest auth route for in-app redirects. This is used by route guards
when a protected page needs to send the user to `/auth` without losing where
they originally wanted to go.
*/
export const buildAuthRoute = ({
  redirectTo,
}: {
  redirectTo?: string | null;
}) => {
  const params = new URLSearchParams();
  const safeRedirectTarget = getSafeRedirectTarget(redirectTo);

  if (safeRedirectTarget) {
    params.set(AUTH_QUERY_PARAMS.REDIRECT, safeRedirectTarget);
  }

  const queryString = params.toString();

  if (!queryString) {
    return AUTH_ROUTES.ROOT;
  }

  return `${AUTH_ROUTES.ROOT}?${queryString}`;
};

/*
Read a redirect target from the current URL. This is the SPA-local channel and
is most useful when guards are bouncing between guest and protected routes in
the same browser session.
*/
export const getRedirectFromSearchParams = (search: string) => {
  const params = new URLSearchParams(search);
  return getSafeRedirectTarget(params.get(AUTH_QUERY_PARAMS.REDIRECT));
};

const canUseSessionStorage = () => {
  return typeof window !== "undefined";
};

/*
Persist the post-auth destination across the full SSO redirect. This is the
bridge between `/auth` before leaving the app and `/auth/success` after the
backend has finished issuing cookies.
*/
export const persistPostAuthRedirect = (
  redirectTarget: string | null | undefined
) => {
  const safeRedirectTarget = getSafeRedirectTarget(redirectTarget);

  if (!canUseSessionStorage()) {
    return;
  }

  if (!safeRedirectTarget) {
    window.sessionStorage.removeItem(POST_AUTH_REDIRECT_STORAGE_KEY);
    return;
  }

  window.sessionStorage.setItem(
    POST_AUTH_REDIRECT_STORAGE_KEY,
    safeRedirectTarget
  );
};

/*
Read and clear the SSO redirect target after auth succeeds. This is consumed
once on the way back into the app so stale redirects do not keep hanging
around in session storage.
*/
export const consumePostAuthRedirect = () => {
  if (!canUseSessionStorage()) {
    return null;
  }

  const redirectTarget = window.sessionStorage.getItem(
    POST_AUTH_REDIRECT_STORAGE_KEY
  );
  window.sessionStorage.removeItem(POST_AUTH_REDIRECT_STORAGE_KEY);
  return getSafeRedirectTarget(redirectTarget);
};
