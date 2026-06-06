export const SUPPORT_EMAIL = "support@ohgraffy.com"

export const APP_URL = import.meta.env.VITE_APP_URL ?? "https://app.ohgraffy.com"

const API_BASE = import.meta.env.VITE_API_URL ?? "https://api.ohgraffy.com"

export const API = {
  billingPlans: new URL("/api/billing/plans", API_BASE).href,
} as const

export const LEGAL_ENTITY = "Classroom X, Inc., a Delaware C Corporation"

export const ROUTES = {
  terms: "/terms",
  privacy: "/privacy",
} as const

export const TIMING = {
  etymologyInterval: 5000,
  etymologyFade: 300,
} as const
