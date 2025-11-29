import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useCallback, useEffect, useState } from "react";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import {
  ACCESS_TOKEN_EXPIRY_TIME,
  AUTH_ROUTES,
  HTTP_STATUS,
} from "./constants";
import authService from "./services/authService";
import AuthLoadingScreen from "./components/AuthLoadingScreen";

const ProtectedLayout = () => {
  const [initialized, setInitialized] = useState(false);
  const navigate = useNavigate();
  const { accessToken, setCheckingAuth, checkingAuth } =
    useAuthContext();

  const refreshAccessToken = useCallback(async () => {
    try {
      await authService.refreshAndSetAccessToken(accessToken);
    } catch (err) {
      const { status } = getAxiosErrorDetails(err);
      if (status === HTTP_STATUS.UNAUTHORIZED) {
        navigate(AUTH_ROUTES.SIGNIN, { replace: true });
      } else {
        throw err;
      }
    } finally {
      setCheckingAuth(false);
    }
  }, [navigate, setCheckingAuth, accessToken]);

  useEffect(() => {
    const initializeAuth = async () => {
      authLogger.debug("Initializing auth");
      try {
        if (accessToken) {
          await authService.fetchCurrentUser();
          authLogger.debug("Access token is valid");
        } else {
          // No token, attempt refresh
          await refreshAccessToken();
        }
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

  useEffect(() => {
    if (!accessToken) return;
    const expiryTimer = setTimeout(() => {
      authLogger.debug("Access token expired, refreshing");
      refreshAccessToken();
      authLogger.debug("Access token refreshed");
    }, ACCESS_TOKEN_EXPIRY_TIME);
    return () => clearTimeout(expiryTimer);
  }, [accessToken, refreshAccessToken]);

  if (checkingAuth || !initialized) {
    return <AuthLoadingScreen />;
  }

  return <Outlet />;
};

export default ProtectedLayout;
