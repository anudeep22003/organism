import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useEffect, useState } from "react";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import { AUTH_ROUTES, HTTP_STATUS } from "./constants";
import authService from "./services/authService";
import AuthLoadingScreen from "./components/AuthLoadingScreen";

const ProtectedLayout = () => {
  const [initialized, setInitialized] = useState(false);
  const navigate = useNavigate();
  const { setCheckingAuth, checkingAuth } = useAuthContext();

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
  }, [initialized]);

  if (checkingAuth || !initialized) {
    return <AuthLoadingScreen />;
  }

  return <Outlet />;
};

export default ProtectedLayout;
