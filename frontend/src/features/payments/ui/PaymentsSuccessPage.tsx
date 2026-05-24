import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import {
  consumeCheckoutReturnPath,
  getReturnPathFromSearchParams,
} from "../routing/payments-redirect";

export default function PaymentsSuccessPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const returnPath =
    getReturnPathFromSearchParams(location.search) ??
    consumeCheckoutReturnPath() ??
    "/stories";

  useEffect(() => {
    void navigate(returnPath, { replace: true });
  }, [navigate, returnPath]);

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
