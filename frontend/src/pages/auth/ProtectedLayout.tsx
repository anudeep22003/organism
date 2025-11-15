import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useCallback, useEffect, useState } from "react";
import useAuthEntry from "./hooks/useAuth";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";

const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { accessToken, setAccessToken } = useAuthContext();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const { getRefreshedAccessToken, getUser } = useAuthEntry();

  const refreshAccessToken = useCallback(async () => {
    try {
      const response = await getRefreshedAccessToken();
      setAccessToken(response.accessToken);
      authLogger.debug("Access token refreshed", response);
    } catch (err) {
      const { status } = getAxiosErrorDetails(err);
      if (status === 401) {
        navigate("/auth?tab=signin", { replace: true });
      } else {
        throw err;
      }
    } finally {
      setCheckingAuth(false);
    }
  }, [getRefreshedAccessToken, setAccessToken, navigate]);

  useEffect(() => {
    const checkAuth = async () => {
      if (accessToken) {
        try {
          const response = await getUser(accessToken);
          authLogger.debug("User", response);
          authLogger.debug("Access token is valid");
          return;
        } catch (err) {
          const { status } = getAxiosErrorDetails(err);
          if (status === 401) {
            await refreshAccessToken();
          } else {
            throw err;
          }
        }
      }
      if (!accessToken) {
        await refreshAccessToken();
      }
    };
    checkAuth();
  }, [
    accessToken,
    refreshAccessToken,
    navigate,
    setAccessToken,
    getUser,
  ]);

  if (checkingAuth) {
    return <div>Checking Auth...</div>;
  }

  return <Outlet />;
};

export default ProtectedLayout;
