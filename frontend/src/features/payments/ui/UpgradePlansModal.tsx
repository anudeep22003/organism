import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { plansOptions } from "../api/payments.queries";
import { paymentsApi } from "../api/payments.api";
import type { Plan } from "../payments.types";
import PlansCatalog from "./PlansCatalog";

export default function UpgradePlansModal({
  open,
  onDismiss,
  requiredFeature,
  returnPath,
}: {
  open: boolean;
  onDismiss: () => void;
  requiredFeature: string | null;
  returnPath: string | null;
}) {
  const { data, isLoading, isError } = useQuery({
    ...plansOptions(),
    enabled: open,
  });
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      return;
    }

    setActivePlanId(null);
    setIsSubmitting(false);
    setErrorMessage(null);
  }, [open]);

  const handleSelectPlan = async (plan: Plan) => {
    setErrorMessage(null);
    setActivePlanId(plan.planId);
    setIsSubmitting(true);

    try {
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
    <AlertDialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          onDismiss();
        }
      }}
    >
      <AlertDialogContent className="max-w-4xl overflow-y-auto">
        <AlertDialogHeader>
          <AlertDialogTitle>Upgrade required</AlertDialogTitle>
          <AlertDialogDescription>
            {requiredFeature
              ? `This action requires the ${requiredFeature} entitlement. Choose a plan to continue.`
              : "Choose a plan to unlock this action."}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {isLoading ? (
          <div className="border border-border bg-background p-6 text-sm text-muted-foreground">
            Loading plans...
          </div>
        ) : null}

        {isError ? (
          <div className="border border-destructive/20 bg-background p-6 text-sm text-destructive">
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
          <div className="border border-destructive/20 bg-background p-4 text-sm text-destructive">
            {errorMessage}
          </div>
        ) : null}

        <AlertDialogFooter>
          <AlertDialogCancel>Not now</AlertDialogCancel>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
