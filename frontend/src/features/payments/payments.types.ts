export type BillingErrorCode = "billing_entitlement_required";

export type BillingEntitlementRequiredError = {
  code: BillingErrorCode;
  requiredFeature: string;
};

export type BillingRecommendedAction =
  | "subscribe"
  | "resubscribe"
  | "trial_active"
  | "manage_subscription"
  | "payment_failed"
  | "none";

export type BillingSubscriptionStatus =
  | "incomplete"
  | "incomplete_expired"
  | "trialing"
  | "active"
  | "past_due"
  | "unpaid"
  | "paused"
  | "canceled";

export type BillingEntitlementSummary = {
  feature: string;
  validUntil: string | null;
};

export type BillingSubscriptionSummary = {
  status: BillingSubscriptionStatus;
  planId: string | null;
  planName: string | null;
  currentPeriodEnd: string;
  renewsOn: string | null;
  validUntil: string | null;
  trialEndsAt: string | null;
  cancelAtPeriodEnd: boolean;
};

export type BillingMeResponse = {
  hasStripeCustomer: boolean;
  hasActiveEntitlement: boolean;
  activeEntitlements: BillingEntitlementSummary[];
  subscription: BillingSubscriptionSummary | null;
  canStartCheckout: boolean;
  recommendedAction: BillingRecommendedAction;
};

export type BillingPortalResponse = {
  portalUrl: string;
};

export type PlanFeature = {
  label: string;
  description: string | null;
};

export type PlanPrice = {
  amountMinor: number;
  currency: string;
  interval: string;
};

export type Plan = {
  planId: string;
  displayName: string;
  description: string | null;
  features: PlanFeature[];
  price: PlanPrice;
};

export type ListPlansResponse = {
  plans: Plan[];
};

export type CreateCheckoutSessionRequest = {
  planId: string;
  returnPath?: string | null;
};

export type CreateCheckoutSessionResponse = {
  checkoutUrl: string;
};
