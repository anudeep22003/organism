import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { AUTH_ROUTES } from "./constants";
import { useEffect } from "react";
import { authLogger } from "@/lib/logger";

const PublicLayout = () => {
  const { accessToken, checkingAuth } = useAuthContext();
  const navigate = useNavigate();

  useEffect(() => {
    authLogger.debug("Checking Auth", { accessToken, checkingAuth });
    if (!checkingAuth && accessToken) {
      navigate(AUTH_ROUTES.HOME);
    }
  }, [accessToken, navigate, checkingAuth]);

  // TODO: When logout is implemented, uncomment this
  // if (checkingAuth) {
  //   return <div>Checking Auth...</div>;
  // }

  return <Outlet />;
};

export default PublicLayout;
