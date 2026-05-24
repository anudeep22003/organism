import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { billingMeOptions } from "../api/payments.queries";
import { BILLING_PORTAL_URL } from "../payments.constants";
import {
  formatBillingDate,
  getBillingAccountCopy,
} from "../payments.utils";

const Field = ({
  label,
  value,
}: {
  label: string;
  value: string;
}) => (
  <div className="space-y-1">
    <span className="text-xs text-muted-foreground">{label}</span>
    <p className="text-sm text-foreground">{value}</p>
  </div>
);

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

  const copy = getBillingAccountCopy(data);
  const subscription = data.subscription;

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
        <Field label="Plan" value={subscription?.planName ?? "No plan"} />
        <Field
          label="Status"
          value={subscription?.status ?? "none"}
        />
        <Field
          label="Entitlement"
          value={data.hasActiveEntitlement ? "Active" : "Not active"}
        />
        <Field
          label="Access valid until"
          value={
            formatBillingDate(subscription?.validUntil ?? null) ??
            "Not available"
          }
        />
      </div>

      {data.activeEntitlements.length > 0 ? (
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">
            Active entitlements
          </span>
          <div className="flex flex-col gap-2">
            {data.activeEntitlements.map((entitlement) => (
              <div
                key={`${entitlement.feature}-${entitlement.validUntil ?? "open"}`}
                className="flex items-center justify-between gap-4 border border-border px-3 py-2"
              >
                <span className="text-sm text-foreground">
                  {entitlement.feature}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatBillingDate(entitlement.validUntil) ??
                    "Open ended"}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {copy.ctaKind === "plans" && copy.ctaLabel ? (
        <Button
          type="button"
          disabled={!data.canStartCheckout}
          onClick={() =>
            void navigate("/payments?returnPath=%2Faccount")
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
