import { Button } from "@/components/ui/button";
import type { Plan } from "../payments.types";
import { formatPlanInterval, formatPlanPrice } from "../payments.utils";

type PlansCatalogProps = {
  activePlanId?: string | null;
  isSubmitting?: boolean;
  onSelectPlan: (plan: Plan) => void;
  plans: Plan[];
};

export default function PlansCatalog({
  activePlanId,
  isSubmitting = false,
  onSelectPlan,
  plans,
}: PlansCatalogProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {plans.map((plan) => {
        const isActive = activePlanId === plan.planId;

        return (
          <div
            key={plan.planId}
            className="flex h-full flex-col gap-6 border border-border bg-background p-6 shadow-sm"
          >
            <div className="space-y-2">
              <div className="space-y-1">
                <h2 className="text-lg font-medium text-foreground">
                  {plan.displayName}
                </h2>
                {plan.description ? (
                  <p className="text-sm text-muted-foreground">
                    {plan.description}
                  </p>
                ) : null}
              </div>
              <div className="flex items-end gap-1">
                <span className="text-2xl font-semibold text-foreground">
                  {formatPlanPrice(plan.price)}
                </span>
                <span className="pb-0.5 text-sm text-muted-foreground">
                  {formatPlanInterval(plan.price.interval)}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {plan.features.map((feature) => (
                <div
                  key={`${plan.planId}-${feature.label}`}
                  className="space-y-1 border-l border-border pl-3"
                >
                  <p className="text-sm text-foreground">
                    {feature.label}
                  </p>
                  {feature.description ? (
                    <p className="text-xs text-muted-foreground">
                      {feature.description}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>

            <Button
              type="button"
              className="mt-auto"
              onClick={() => onSelectPlan(plan)}
              disabled={isSubmitting}
            >
              {isActive && isSubmitting ? "Redirecting..." : "Choose plan"}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
