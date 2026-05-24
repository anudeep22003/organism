import type { PlanPrice } from "./payments.types";

export const formatPlanPrice = (price: PlanPrice) => {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: price.currency.toUpperCase(),
  }).format(price.amountMinor / 100);
};

export const formatPlanInterval = (interval: string) => {
  return `/${interval}`;
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
