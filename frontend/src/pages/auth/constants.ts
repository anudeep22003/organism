export const AUTH_ROUTES = {
  HOME: "/",
  SIGNIN: "/auth?tab=signin",
  SIGNUP: "/auth?tab=signup",
} as const;

export const AUTH_TABS = {
  SIGNIN: "signin",
  SIGNUP: "signup",
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
