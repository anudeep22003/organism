import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";

export default function PaymentsSuccessPage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-0 flex-1 items-center justify-center p-6">
      <div className="flex w-full max-w-md flex-col gap-6 border border-border bg-background p-6 shadow-sm">
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">Payments</span>
          <h1 className="text-lg font-medium text-foreground">
            Payment complete
          </h1>
          <p className="text-sm text-muted-foreground">
            Your checkout flow finished successfully.
          </p>
        </div>

        <Button
          type="button"
          onClick={() => void navigate("/stories")}
        >
          Back to stories
        </Button>
      </div>
    </div>
  );
}
