export const AUTH_TABS = {
  SIGNIN: "signin",
  SIGNUP: "signup",
} as const;

export const AUTH_ROUTES = {
  HOME: "/",
  SIGNIN: "/auth?tab=" + AUTH_TABS.SIGNIN,
  SIGNUP: "/auth?tab=" + AUTH_TABS.SIGNUP,
} as const;

export const AUTH_FIELDS = {
  EMAIL: "email",
  PASSWORD: "password",
  FULL_NAME: "fullName",
  ACCEPT_TERMS: "acceptTerms",
} as const;

export const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  BAD_REQUEST: 400,
} as const;

export const AUTH_SERVICE_ENDPOINTS = {
  ME: "/api/auth/me",
  SIGNIN: "/api/auth/signin",
  SIGNUP: "/api/auth/signup",
  REFRESH: "/api/auth/refresh",
} as const;

export const ACCESS_TOKEN_EXPIRY_TIME = 1000 * 60 * 30; // 30 minutes
