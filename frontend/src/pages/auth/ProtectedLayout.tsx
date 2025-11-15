import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { useEffect, useState } from "react";
import useAuthEntry from "./hooks/useAuthEntry";
import { authLogger } from "@/lib/logger";

const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { accessToken } = useAuthContext();
  const { doesRefreshTokenExistInCookies } = useAuthEntry();
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      const refreshTokenExists = doesRefreshTokenExistInCookies();
      authLogger.debug("refreshTokenExists: ", refreshTokenExists);
      if (!refreshTokenExists) {
        navigate("/auth");
      }
      setCheckingAuth(false);
    }
  }, []);

  if (checkingAuth) {
    return <div>Checking Auth...</div>;
  }

  return <Outlet />;
};

export default ProtectedLayout;
