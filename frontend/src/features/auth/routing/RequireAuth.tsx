import { Button } from "@/components/ui/button";
import { LogOut, Moon, Sun, User } from "lucide-react";
import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router";
import { AUTH_TABS } from "../api/auth.constants";
import { useAuth } from "../model/auth.context";
import { useTheme } from "@/context/ThemeContext";
import { buildAuthRoute } from "./auth-redirect";
import AuthLoadingScreen from "../ui/components/AuthLoadingScreen";

const HEADER_BUTTON_CLASSES = "size-7 text-muted-foreground hover:text-foreground hover:bg-accent";

const RequireAuth = () => {
  const { status, signOut } = useAuth();
  const { theme, toggleTheme } = useTheme();
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
      <header className="flex w-full justify-end items-center gap-1 px-3 py-1.5 border-b border-border">
        <Button
          size="icon"
          variant="ghost"
          className={HEADER_BUTTON_CLASSES}
          title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          onClick={toggleTheme}
        >
          {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className={HEADER_BUTTON_CLASSES}
          title="Account"
        >
          <User className="size-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          className={HEADER_BUTTON_CLASSES}
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
