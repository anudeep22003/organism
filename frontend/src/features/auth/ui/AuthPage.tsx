import { GoogleIcon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { Link, useLocation } from "react-router";
import { AUTH_ROUTES } from "../api/auth.constants";
import { getRedirectFromSearchParams } from "../routing/auth-redirect";

const AuthPage = () => {
  const location = useLocation();
  const redirectTarget = getRedirectFromSearchParams(location.search);

  const handleGoogleSignIn = () => {
    console.log("Google sign-in clicked", { redirectTarget });
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-1.5">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Organism</span>
          <div className="h-2.5 w-px bg-border" />
          <span className="text-[10px] text-foreground">Sign in</span>
        </div>
        <Link
          to={AUTH_ROUTES.LEGACY}
          className="text-[10px] text-muted-foreground hover:text-foreground"
        >
          Legacy auth
        </Link>
      </div>

      <div className="flex min-h-0 flex-1 items-center justify-center p-4">
        <div className="flex w-full max-w-md flex-col border border-border bg-muted/10">
          <div className="border-b border-border px-4 py-3">
            <span className="text-[10px] text-muted-foreground">
              Authentication
            </span>
          </div>

          <div className="flex flex-col gap-6 px-4 py-6 sm:px-6">
            <div className="space-y-2">
              <h1 className="text-base text-foreground">
                Continue with Google
              </h1>
              <p className="text-xs text-muted-foreground">
                Sign in with your Google account to verify your email and enter
                Organism.
              </p>
              {redirectTarget ? (
                <p className="text-[10px] text-muted-foreground">
                  Redirect after sign-in: {redirectTarget}
                </p>
              ) : null}
            </div>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              className="flex items-center justify-between border border-border bg-background px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted/40"
            >
              <span className="flex items-center gap-2">
                <HugeiconsIcon icon={GoogleIcon} size={16} />
                <span>Continue with Google</span>
              </span>
              <span className="text-[10px] text-muted-foreground">SSO</span>
            </button>

            <p className="text-[10px] text-muted-foreground">
              Google SSO is the new auth path. The legacy email/password screen
              remains available during migration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
