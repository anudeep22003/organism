import { useQuery } from "@tanstack/react-query";
import { plansOptions } from "../api/payments.queries";
import PlansCatalog from "./PlansCatalog";

export default function PublicPlansPage() {
  const { data, isLoading, isError } = useQuery(plansOptions());

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
            onSelectPlan={() => undefined}
          />
        ) : null}
      </div>
    </div>
  );
}
