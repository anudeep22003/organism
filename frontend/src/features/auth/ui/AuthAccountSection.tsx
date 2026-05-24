import { useAuth } from "../model/auth.context";

export default function AuthAccountSection() {
  const { user } = useAuth();

  return (
    <section className="flex flex-col gap-6 border border-border bg-background p-6 shadow-sm">
      <div className="space-y-2">
        <span className="text-xs text-muted-foreground">Profile</span>
        <h2 className="text-lg font-medium text-foreground">
          Identity
        </h2>
        <p className="text-sm text-muted-foreground">
          This information comes from the current authenticated session.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Full name
          </span>
          <p className="text-sm text-foreground">
            {user?.fullName ?? "No name on file"}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Email
          </span>
          <p className="break-all text-sm text-foreground">
            {user?.email ?? "Unknown"}
          </p>
        </div>

        <div className="space-y-1 sm:col-span-2">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            User ID
          </span>
          <p className="break-all font-mono text-xs text-muted-foreground">
            {user?.id ?? "Unavailable"}
          </p>
        </div>
      </div>
    </section>
  );
}
