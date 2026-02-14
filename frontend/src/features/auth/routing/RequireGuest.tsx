import { Navigate, Outlet, useLocation } from "react-router";
import { AUTH_ROUTES } from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import { getRedirectFromSearchParams } from "./auth-redirect";
import AuthLoadingScreen from "../ui/components/AuthLoadingScreen";

const RequireGuest = () => {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "checking") {
    return <AuthLoadingScreen />;
  }

  if (status === "authenticated") {
    const redirectTarget = getRedirectFromSearchParams(
      location.search
    );

    return (
      <Navigate
        to={redirectTarget ?? AUTH_ROUTES.HOME_FALLBACK}
        replace
      />
    );
  }

  return <Outlet />;
};

export default RequireGuest;
