import { Navigate, Outlet, useLocation } from "react-router";
import { AUTH_TABS } from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import { buildAuthRoute } from "./auth-redirect";
import AuthLoadingScreen from "../ui/components/AuthLoadingScreen";

const RequireAuth = () => {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "checking") {
    return <AuthLoadingScreen />;
  }

  if (status === "unauthenticated") {
    const currentPath = `${location.pathname}${location.search}${location.hash}`;
    return (
      <Navigate
        to={buildAuthRoute({ tab: AUTH_TABS.SIGNIN, redirectTo: currentPath })}
        replace
      />
    );
  }

  return <Outlet />;
};

export default RequireAuth;
