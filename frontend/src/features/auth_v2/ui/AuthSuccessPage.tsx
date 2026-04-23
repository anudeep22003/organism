import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router";
import { AUTH_V2_ROUTES } from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import {
  consumePostAuthRedirect,
  getRedirectFromSearchParams,
} from "../routing/auth-redirect";
import AuthOutcomePage from "./AuthOutcomePage";
import AuthLoadingScreen from "./components/AuthLoadingScreen";

const AuthSuccessPage = () => {
  const { isAuthenticated, isLoading, refreshSession, status } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const bootstrapAttemptedRef = useRef(false);

  useEffect(() => {
    if (bootstrapAttemptedRef.current) {
      return;
    }

    bootstrapAttemptedRef.current = true;
    void refreshSession();
  }, [refreshSession]);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (isAuthenticated) {
      const redirectTarget =
        consumePostAuthRedirect() ??
        getRedirectFromSearchParams(location.search) ??
        AUTH_V2_ROUTES.HOME_FALLBACK;

      void navigate(redirectTarget, { replace: true });
      return;
    }

    if (status === "unauthenticated") {
      void navigate(AUTH_V2_ROUTES.FAILURE, { replace: true });
    }
  }, [isAuthenticated, isLoading, location.search, navigate, status]);

  if (isLoading) {
    return (
      <AuthLoadingScreen
        title="Completing sign in"
        description="Finalizing your session and bringing you into the app."
      />
    );
  }

  return (
    <AuthOutcomePage
      title="Sign in complete"
      description="Your session is ready. Redirecting you into the app."
    >
      <div className="border border-border bg-background/80 px-4 py-3 text-xs text-muted-foreground">
        You should be redirected automatically.
      </div>
    </AuthOutcomePage>
  );
};

export default AuthSuccessPage;
