import { useState } from "react";
import { Button } from "@/components/ui/button";
import { paymentsApi } from "../api/payments.api";

export default function PaymentsPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handlePay = async () => {
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await paymentsApi.startCheckout();
    } catch {
      setErrorMessage("Unable to start checkout. Try again.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 items-center justify-center p-6">
      <div className="flex w-full max-w-md flex-col gap-6 border border-border bg-background p-6 shadow-sm">
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">Payments</span>
          <h1 className="text-lg font-medium text-foreground">
            Test checkout
          </h1>
          <p className="text-sm text-muted-foreground">
            Start a checkout session and continue in the hosted payment
            flow.
          </p>
        </div>

        <Button
          type="button"
          onClick={() => void handlePay()}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Redirecting..." : "Pay"}
        </Button>

        {errorMessage ? (
          <p className="text-sm text-destructive">{errorMessage}</p>
        ) : null}
      </div>
    </div>
  );
}
