import { Button } from "@/components/ui/button";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import { LogOut, User } from "lucide-react";
import { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router";
import AuthLoadingScreen from "./components/AuthLoadingScreen";
import { AUTH_ROUTES, HTTP_STATUS } from "./constants";
import { useAuthContext } from "./context";
import authService from "./services/authService";

const ProtectedLayout = () => {
  const [initialized, setInitialized] = useState(false);
  const navigate = useNavigate();
  const { setCheckingAuth, checkingAuth, accessToken } =
    useAuthContext();

  useEffect(() => {
    // only check after initialiazation to avoid interfering with initial auth check
    if (initialized && accessToken === null) {
      authLogger.debug("Access token is null. Navigating to signin.");
      navigate(AUTH_ROUTES.SIGNIN, { replace: true });
    }
  }, [accessToken, initialized, navigate]);

  useEffect(() => {
    const initializeAuth = async () => {
      authLogger.debug("Initializing auth");
      try {
        // The httpClient's interceptors will automatically handle token refresh on 401 errors
        // and retry the request. If the refresh fails, the request will fail with 401.
        await authService.fetchCurrentUser();
      } catch (err) {
        const { status } = getAxiosErrorDetails(err);
        if (status === HTTP_STATUS.UNAUTHORIZED) {
          navigate(AUTH_ROUTES.SIGNIN, { replace: true });

          authLogger.error("Auth check failed:", err);
        } else {
          throw err;
        }
      } finally {
        setCheckingAuth(false);
        setInitialized(true);
      }
    };

    if (!initialized) {
      initializeAuth();
    }
  }, [initialized, navigate, setCheckingAuth]);

  if (checkingAuth || !initialized) {
    return <AuthLoadingScreen />;
  }

  return (
    <>
      <header className="flex w-full justify-end items-center gap-1 px-3 py-1.5 border-b border-neutral-200">
        <Button
          size="icon"
          variant="ghost"
          className="size-7 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100"
          title="Account"
        >
          <User className="size-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="size-7 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100"
          title="Logout"
          onClick={() => authService.logoutUserAndClearAccessToken()}
        >
          <LogOut className="size-4" />
        </Button>
      </header>
      <Outlet />
    </>
  );
};

export default ProtectedLayout;
