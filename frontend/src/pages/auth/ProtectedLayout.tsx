import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useCallback, useEffect } from "react";
import useAuthEntry from "./hooks/useAuth";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import { AUTH_ROUTES, HTTP_STATUS } from "./constants";

const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { accessToken, setAccessToken, setCheckingAuth, checkingAuth } =
    useAuthContext();
  const { getRefreshedAccessToken, getUser } = useAuthEntry();

  const refreshAccessToken = useCallback(async () => {
    try {
      const response = await getRefreshedAccessToken(accessToken);
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
  }, [
    getRefreshedAccessToken,
    setAccessToken,
    navigate,
    setCheckingAuth,
    accessToken,
  ]);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (accessToken) {
          try {
            const response = await getUser(accessToken);
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
  }, [
    accessToken,
    refreshAccessToken,
    getUser,
    navigate,
    setCheckingAuth,
  ]);

  if (checkingAuth) {
    return <div>Checking Auth...</div>;
  }

  return <Outlet />;
};

export default ProtectedLayout;
