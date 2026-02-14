import { Button } from "@/components/ui/button";
import { LogOut, User } from "lucide-react";
import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router";
import { AUTH_TABS } from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import { buildAuthRoute } from "./auth-redirect";
import AuthLoadingScreen from "../ui/components/AuthLoadingScreen";

const RequireAuth = () => {
  const { status, signOut } = useAuth();
  const location = useLocation();

  if (status === "checking") {
    return <AuthLoadingScreen />;
  }

  if (status === "unauthenticated") {
    const currentPath = `${location.pathname}${location.search}${location.hash}`;

    return (
      <Navigate
        to={buildAuthRoute({
          tab: AUTH_TABS.SIGNIN,
          redirectTo: currentPath,
        })}
        replace
      />
    );
  }

  return (
    <>
      <header className="flex w-full justify-end items-center gap-1 px-3 py-1.5 border-b border-neutral-200">
        <Button
          size="icon"
          variant="ghost"
          className="size-7 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100"
          title="Account"
        >
          <User className="size-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className="size-7 text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100"
          title="Logout"
          onClick={() => {
            void signOut();
          }}
        >
          <LogOut className="size-4" />
        </Button>
      </header>
      <Outlet />
    </>
  );
};

export default RequireAuth;
