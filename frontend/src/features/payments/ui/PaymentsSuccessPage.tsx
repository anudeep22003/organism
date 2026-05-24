import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { PAYMENTS_QUERY_ROOT } from "../payments.constants";
import {
  consumeCheckoutReturnPath,
  getReturnPathFromSearchParams,
} from "../routing/payments-redirect";

export default function PaymentsSuccessPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const location = useLocation();
  const returnPath =
    getReturnPathFromSearchParams(location.search) ??
    consumeCheckoutReturnPath() ??
    "/stories";

  useEffect(() => {
    void queryClient.invalidateQueries({ queryKey: PAYMENTS_QUERY_ROOT });
    void navigate(returnPath, { replace: true });
  }, [navigate, queryClient, returnPath]);

  return (
    <div className="flex min-h-0 flex-1 items-center justify-center p-6">
      <div className="flex w-full max-w-md flex-col gap-6 border border-border bg-background p-6 shadow-sm">
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">Payments</span>
          <h1 className="text-lg font-medium text-foreground">
            Payment complete
          </h1>
          <p className="text-sm text-muted-foreground">
            Your checkout flow finished successfully. Redirecting you back
            into the app.
          </p>
        </div>

        <Button
          type="button"
          onClick={() => void navigate(returnPath, { replace: true })}
        >
          Continue
        </Button>
      </div>
    </div>
  );
}
