export const AUTH_TABS = {
  SIGNIN: "signin",
  SIGNUP: "signup",
} as const;

export type AuthTab = (typeof AUTH_TABS)[keyof typeof AUTH_TABS];

export const AUTH_QUERY_PARAMS = {
  TAB: "tab",
  REDIRECT: "redirect",
} as const;

export const AUTH_FIELDS = {
  EMAIL: "email",
  PASSWORD: "password",
  FULL_NAME: "fullName",
  ACCEPT_TERMS: "acceptTerms",
} as const;

export const AUTH_SERVICE_ENDPOINTS = {
  ME: "/api/legacy-auth/me",
  SIGNIN: "/api/legacy-auth/signin",
  SIGNUP: "/api/legacy-auth/signup",
  REFRESH: "/api/legacy-auth/refresh",
  LOGOUT: "/api/legacy-auth/logout",
} as const;

export const AUTH_ROUTES = {
  ROOT: "/auth",
  LEGACY: "/auth/legacy",
  HOME_FALLBACK: "/",
} as const;

export const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  BAD_REQUEST: 400,
  NO_CONTENT: 204,
} as const;

export const ACCESS_TOKEN_EXPIRY_TIME = 1000 * 60 * 30;
