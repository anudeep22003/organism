import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router";
import { plansOptions } from "../api/payments.queries";
import { paymentsApi } from "../api/payments.api";
import type { Plan } from "../payments.types";
import {
  getReturnPathFromSearchParams,
  getSafeReturnPath,
} from "../routing/payments-redirect";
import PlansCatalog from "./PlansCatalog";

export default function PaymentsPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const location = useLocation();
  const { data, isLoading, isError } = useQuery(plansOptions());

  const handleSelectPlan = async (plan: Plan) => {
    setErrorMessage(null);
    setActivePlanId(plan.planId);
    setIsSubmitting(true);

    try {
      const returnPath =
        getReturnPathFromSearchParams(location.search) ??
        getSafeReturnPath(location.pathname);

      await paymentsApi.startCheckout({
        planId: plan.planId,
        returnPath,
      });
    } catch {
      setErrorMessage("Unable to start checkout. Try again.");
      setActivePlanId(null);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6 p-6">
      <div className="space-y-2">
        <span className="text-xs text-muted-foreground">Payments</span>
        <h1 className="text-xl font-medium text-foreground">
          Choose a plan
        </h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Plans come from the billing service. Select one to continue to
          Stripe checkout.
        </p>
      </div>

      {isLoading ? (
        <div className="border border-border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Loading plans...
        </div>
      ) : null}

      {isError ? (
        <div className="border border-destructive/20 bg-background p-6 text-sm text-destructive shadow-sm">
          Unable to load plans right now.
        </div>
      ) : null}

      {data ? (
        <PlansCatalog
          plans={data.plans}
          activePlanId={activePlanId}
          isSubmitting={isSubmitting}
          onSelectPlan={(plan) => void handleSelectPlan(plan)}
        />
      ) : null}

      {errorMessage ? (
        <div className="border border-destructive/20 bg-background p-4 text-sm text-destructive shadow-sm">
          {errorMessage}
        </div>
      ) : null}
    </div>
  );
}
