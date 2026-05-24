import type { BillingMeResponse, PlanPrice } from "./payments.types";

export type BillingAccountCtaKind = "plans" | "portal";

export type BillingAccountCopy = {
  title: string;
  description: string;
  ctaLabel: string | null;
  ctaKind: BillingAccountCtaKind | null;
};

export const getBillingAccountCopy = (
  billing: BillingMeResponse
): BillingAccountCopy => {
  switch (billing.recommendedAction) {
    case "subscribe":
      return {
        title: "No active plan",
        description:
          "Choose a plan to start billing for this workspace.",
        ctaLabel: "Choose a plan",
        ctaKind: "plans",
      };
    case "resubscribe":
      return {
        title: "Access expired",
        description: "Pick a plan to restore subscription access.",
        ctaLabel: "Choose a plan",
        ctaKind: "plans",
      };
    case "manage_subscription":
      return {
        title: "Subscription active",
        description: "Use the customer portal for billing changes.",
        ctaLabel: "Manage subscription",
        ctaKind: "portal",
      };
    case "payment_failed":
      return {
        title: "Payment recovery needed",
        description: "Update billing details to recover access.",
        ctaLabel: "Fix billing",
        ctaKind: "portal",
      };
    case "trial_active":
      return {
        title: "Trial active",
        description: "Your trial currently grants access.",
        ctaLabel: null,
        ctaKind: null,
      };
    case "none":
    default:
      return {
        title: "Billing in good standing",
        description: "No billing action is required right now.",
        ctaLabel: null,
        ctaKind: null,
      };
  }
};

export const formatBillingDate = (value: string | null) => {
  if (!value) {
    return null;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
};

export const formatPlanPrice = (price: PlanPrice) => {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: price.currency.toUpperCase(),
  }).format(price.amountMinor / 100);
};

export const formatPlanInterval = (interval: string) => {
  return `/${interval}`;
};
