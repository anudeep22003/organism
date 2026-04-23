export const AUTH_SERVICE_ENDPOINTS = {
  LOGIN: "/api/auth/login",
  ME: "/api/auth/me",
  REFRESH: "/api/auth/refresh",
  LOGOUT: "/api/auth/logout",
} as const;

export const AUTH_QUERY_PARAMS = {
  REDIRECT: "redirect",
} as const;

export const AUTH_ROUTES = {
  ROOT: "/auth",
  SUCCESS: "/auth/success",
  FAILURE: "/auth/failure",
  HOME_FALLBACK: "/",
} as const;

export const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NO_CONTENT: 204,
} as const;
