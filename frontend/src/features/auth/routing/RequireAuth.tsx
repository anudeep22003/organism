import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "../model/auth.context";
import AuthLoadingScreen from "../ui/components/AuthLoadingScreen";
import { buildAuthRoute } from "./auth-redirect";

const RequireAuth = () => {
  const { isLoading, status } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <AuthLoadingScreen />;
  }

  if (status === "unauthenticated") {
    const currentPath = `${location.pathname}${location.search}${location.hash}`;

    return (
      <Navigate
        to={buildAuthRoute({ redirectTo: currentPath })}
        replace
      />
    );
  }

  return <Outlet />;
};

export default RequireAuth;
