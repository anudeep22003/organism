import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useCallback, useEffect } from "react";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import { AUTH_ROUTES, HTTP_STATUS } from "./constants";
import authService from "./services/authService";
import AuthLoadingScreen from "./components/AuthLoadingScreen";

const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { accessToken, setAccessToken, setCheckingAuth, checkingAuth } =
    useAuthContext();

  const refreshAccessToken = useCallback(async () => {
    try {
      const response = await authService.refreshAccessToken(
        accessToken
      );
      setAccessToken(response.accessToken);
      authLogger.debug("Access token refreshed", response);
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
  }, [setAccessToken, navigate, setCheckingAuth, accessToken]);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (accessToken) {
          try {
            const response = await authService.fetchCurrentUser(
              accessToken
            );
            authLogger.debug("User", response);
            authLogger.debug("Access token is valid");
            setCheckingAuth(false);
            return;
          } catch (err) {
            const { status } = getAxiosErrorDetails(err);
            if (status === HTTP_STATUS.UNAUTHORIZED) {
              await refreshAccessToken();
            } else {
              throw err;
            }
          }
        } else {
          await refreshAccessToken();
        }
      } catch (err) {
        authLogger.error("Auth check failed:", err);
        setCheckingAuth(false);
        navigate(AUTH_ROUTES.SIGNIN, { replace: true });
      }
    };
    checkAuth();
  }, [accessToken, refreshAccessToken, navigate, setCheckingAuth]);

  if (checkingAuth) {
    return <AuthLoadingScreen />;
  }

  return <Outlet />;
};

export default ProtectedLayout;
