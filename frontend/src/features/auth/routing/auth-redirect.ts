import {
  AUTH_QUERY_PARAMS,
  AUTH_ROUTES,
} from "../api/auth.constants";

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

export const getRedirectFromSearchParams = (search: string) => {
  const params = new URLSearchParams(search);
  return getSafeRedirectTarget(params.get(AUTH_QUERY_PARAMS.REDIRECT));
};

const canUseSessionStorage = () => {
  return typeof window !== "undefined";
};

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
