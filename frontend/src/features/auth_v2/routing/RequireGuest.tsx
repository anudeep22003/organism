import { Navigate, Outlet, useLocation } from "react-router";
import { AUTH_V2_ROUTES } from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import AuthLoadingScreen from "../ui/components/AuthLoadingScreen";
import { getRedirectFromSearchParams } from "./auth-redirect";

const RequireGuest = () => {
  const { isLoading, status } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <AuthLoadingScreen />;
  }

  if (status === "authenticated") {
    const redirectTarget =
      getRedirectFromSearchParams(location.search) ??
      AUTH_V2_ROUTES.HOME_FALLBACK;

    return <Navigate to={redirectTarget} replace />;
  }

  return <Outlet />;
};

export default RequireGuest;
