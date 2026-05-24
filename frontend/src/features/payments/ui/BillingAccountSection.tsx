import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { billingMeOptions } from "../api/payments.queries";
import { BILLING_PORTAL_URL } from "../payments.constants";
import type { BillingMeResponse } from "../payments.types";
import { buildPaymentsRoute } from "../routing/payments-redirect";
import { formatBillingDate } from "../payments.utils";

const billingAccountCopy = (billing: BillingMeResponse) => {
  switch (billing.recommendedAction) {
    case "subscribe":
      return {
        title: "No active plan",
        description:
          "You do not have an active subscription yet. Choose a plan to start billing.",
        ctaLabel: "Choose a plan",
        ctaKind: "plans" as const,
      };
    case "resubscribe":
      return {
        title: "Access expired",
        description:
          "Your prior subscription no longer grants access. Pick a plan to resubscribe.",
        ctaLabel: "Choose a plan",
        ctaKind: "plans" as const,
      };
    case "manage_subscription":
      return {
        title: "Subscription active",
        description:
          "Your billing is active. Use the customer portal for changes and cancellations.",
        ctaLabel: "Manage subscription",
        ctaKind: "portal" as const,
      };
    case "payment_failed":
      return {
        title: "Payment recovery needed",
        description:
          "Your subscription needs billing attention before access can recover.",
        ctaLabel: "Fix billing",
        ctaKind: "portal" as const,
      };
    case "trial_active":
      return {
        title: "Trial active",
        description:
          "Your trial is still active. Billing details will matter when the trial ends.",
        ctaLabel: null,
        ctaKind: null,
      };
    case "none":
    default:
      return {
        title: "Billing in good standing",
        description:
          "No billing action is required right now.",
        ctaLabel: null,
        ctaKind: null,
      };
  }
};

export default function BillingAccountSection() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery(billingMeOptions());

  if (isLoading) {
    return (
      <section className="flex flex-col gap-4 border border-border bg-background p-6 shadow-sm">
        <span className="text-xs text-muted-foreground">Billing</span>
        <p className="text-sm text-muted-foreground">
          Loading billing details...
        </p>
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="flex flex-col gap-4 border border-destructive/20 bg-background p-6 shadow-sm">
        <span className="text-xs text-muted-foreground">Billing</span>
        <p className="text-sm text-destructive">
          Unable to load your billing details right now.
        </p>
      </section>
    );
  }

  const copy = billingAccountCopy(data);
  const periodEnd = formatBillingDate(data.subscription?.currentPeriodEnd ?? null);
  const renewsOn = formatBillingDate(data.subscription?.renewsOn ?? null);
  const validUntil = formatBillingDate(data.subscription?.validUntil ?? null);
  const trialEndsAt = formatBillingDate(data.subscription?.trialEndsAt ?? null);

  return (
    <section className="flex flex-col gap-6 border border-border bg-background p-6 shadow-sm">
      <div className="space-y-2">
        <span className="text-xs text-muted-foreground">Billing</span>
        <h2 className="text-lg font-medium text-foreground">
          {copy.title}
        </h2>
        <p className="text-sm text-muted-foreground">
          {copy.description}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Recommended action
          </span>
          <p className="text-sm text-foreground">
            {data.recommendedAction}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Checkout available
          </span>
          <p className="text-sm text-foreground">
            {data.canStartCheckout ? "Yes" : "No"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Current plan
          </span>
          <p className="text-sm text-foreground">
            {data.subscription?.planName ?? "No plan"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Subscription status
          </span>
          <p className="text-sm text-foreground">
            {data.subscription?.status ?? "none"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Current period end
          </span>
          <p className="text-sm text-foreground">
            {periodEnd ?? "Not available"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Renews on
          </span>
          <p className="text-sm text-foreground">
            {renewsOn ?? "Not scheduled"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Access valid until
          </span>
          <p className="text-sm text-foreground">
            {validUntil ?? "No active entitlement window"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Trial ends
          </span>
          <p className="text-sm text-foreground">
            {trialEndsAt ?? "No active trial"}
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Active entitlements
        </span>
        {data.activeEntitlements.length > 0 ? (
          <div className="space-y-2">
            {data.activeEntitlements.map((entitlement) => (
              <div
                key={`${entitlement.feature}-${entitlement.validUntil ?? "open"}`}
                className="flex items-center justify-between gap-4 border border-border px-3 py-2"
              >
                <span className="text-sm text-foreground">
                  {entitlement.feature}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatBillingDate(entitlement.validUntil) ?? "Open ended"}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No active entitlements.
          </p>
        )}
      </div>

      {copy.ctaKind === "plans" && copy.ctaLabel ? (
        <Button
          type="button"
          onClick={() =>
            void navigate(buildPaymentsRoute({ returnPath: "/account" }))
          }
        >
          {copy.ctaLabel}
        </Button>
      ) : null}

      {copy.ctaKind === "portal" && copy.ctaLabel ? (
        <Button asChild>
          <a
            href={BILLING_PORTAL_URL}
            target="_blank"
            rel="noreferrer"
          >
            {copy.ctaLabel}
          </a>
        </Button>
      ) : null}
    </section>
  );
}
