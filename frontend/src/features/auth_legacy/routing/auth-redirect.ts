import {
  AUTH_QUERY_PARAMS,
  AUTH_ROUTES,
  AUTH_TABS,
  type AuthTab,
} from "../api/auth.constants";

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
  tab,
  redirectTo,
}: {
  tab: AuthTab;
  redirectTo?: string | null;
}) => {
  const params = new URLSearchParams({
    [AUTH_QUERY_PARAMS.TAB]: tab,
  });

  const safeRedirectTarget = getSafeRedirectTarget(redirectTo);
  if (safeRedirectTarget) {
    params.set(AUTH_QUERY_PARAMS.REDIRECT, safeRedirectTarget);
  }

  return `${AUTH_ROUTES.ROOT}?${params.toString()}`;
};

export const getAuthTabFromSearchParams = (search: string): AuthTab => {
  const params = new URLSearchParams(search);
  const tab = params.get(AUTH_QUERY_PARAMS.TAB);
  if (tab === AUTH_TABS.SIGNUP) {
    return AUTH_TABS.SIGNUP;
  }
  return AUTH_TABS.SIGNIN;
};

export const getRedirectFromSearchParams = (search: string) => {
  const params = new URLSearchParams(search);
  return getSafeRedirectTarget(params.get(AUTH_QUERY_PARAMS.REDIRECT));
};
