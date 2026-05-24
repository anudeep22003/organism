export default function AccountPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6 p-6">
      <div className="space-y-2">
        <span className="text-xs text-muted-foreground">Account</span>
        <h1 className="text-xl font-medium text-foreground">
          Your account
        </h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Manage profile details and billing controls for your workspace.
        </p>
      </div>
    </div>
  );
}
