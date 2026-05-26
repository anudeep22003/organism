import { useState } from "react";
import { buildAuthRoute, useAuth } from "@/features/auth";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { paymentsApi } from "../api/payments.api";
import { plansOptions } from "../api/payments.queries";
import type { Plan } from "../payments.types";
import PlansCatalog from "./PlansCatalog";

export default function PublicPlansPage() {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { data, isLoading, isError } = useQuery(plansOptions());

  const handleSelectPlan = async (plan: Plan) => {
    if (isAuthLoading) {
      return;
    }

    if (!isAuthenticated) {
      void navigate(buildAuthRoute({ redirectTo: "/plans" }));
      return;
    }

    setActivePlanId(plan.planId);
    setErrorMessage(null);

    try {
      await paymentsApi.startCheckout({
        planId: plan.planId,
        returnPath: "/plans",
      });
    } catch {
      setActivePlanId(null);
      setErrorMessage("Unable to start checkout. Try again.");
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">Plans</span>
          <h1 className="text-xl font-medium text-foreground">
            Public plans test
          </h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            This page reads the public billing plans endpoint without
            requiring sign in.
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
            onSelectPlan={handleSelectPlan}
            activePlanId={activePlanId}
            isSubmitting={Boolean(activePlanId) || isAuthLoading}
          />
        ) : null}

        {errorMessage ? (
          <div className="border border-destructive/20 bg-background p-4 text-sm text-destructive shadow-sm">
            {errorMessage}
          </div>
        ) : null}
      </div>
    </div>
  );
}
