import { Outlet, useNavigate } from "react-router";
import { useAuthContext } from "./context";
import { Suspense, useEffect, useState } from "react";

const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { accessToken } = useAuthContext();
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      navigate("/auth");
    }
  }, []);

  if (checkingAuth) {
    return <div>Checking Auth...</div>;
  }

  return <Outlet />;
};

export default ProtectedLayout;
