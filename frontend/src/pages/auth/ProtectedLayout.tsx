import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useEffect, useState } from "react";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import { AUTH_ROUTES, HTTP_STATUS } from "./constants";
import authService from "./services/authService";
import AuthLoadingScreen from "./components/AuthLoadingScreen";
import { Button } from "@/components/ui/button";

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
  }, [initialized]);

  if (checkingAuth || !initialized) {
    return <AuthLoadingScreen />;
  }

  return (
    <>
      <div className="bg-gray-200 gap-2 flex w-full p-2 justify-end items-center">
        <Button
          size={"sm"}
          onClick={() => authService.logoutUserAndClearAccessToken()}
        >
          Logout
        </Button>
        <Button size={"sm"}>Show Account</Button>
      </div>
      <Outlet />
    </>
  );
};

export default ProtectedLayout;
