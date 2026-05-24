import AuthAccountSection from "@/features/auth/ui/AuthAccountSection";
import BillingAccountSection from "@/features/payments/ui/BillingAccountSection";

export default function AccountPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6 p-6">
      <div className="space-y-2">
        <span className="text-xs text-muted-foreground">Account</span>
        <h1 className="text-xl font-medium text-foreground">
          Your account
        </h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Manage profile details and the billing controls attached to
          your workspace.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <AuthAccountSection />
        <BillingAccountSection />
      </div>
    </div>
  );
}
