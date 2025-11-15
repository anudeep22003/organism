import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useEffect, useState } from "react";
import useAuthEntry from "./hooks/useAuth";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";

const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { accessToken, setAccessToken } = useAuthContext();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const { refreshAccessToken } = useAuthEntry();

  useEffect(() => {
    const checkAuth = async () => {
      if (!accessToken) {
        try {
          const response = await refreshAccessToken();
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
      }
    };
    checkAuth();
  }, [accessToken, refreshAccessToken, navigate, setAccessToken]);

  if (checkingAuth) {
    return <div>Checking Auth...</div>;
  }

  return <Outlet />;
};

export default ProtectedLayout;
