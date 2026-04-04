import { Button } from "@/components/ui/button";
import { useTheme } from "@/context/ThemeContext";
import { LogOut, Moon, Sun, User } from "lucide-react";
import { Outlet } from "react-router";
import { useAuth } from "../auth/model/auth.context";

const CONTROL_CLASSES = "size-7 text-muted-foreground hover:text-foreground hover:bg-accent";

export default function SceneEngineLayout() {
  const { signOut } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen flex-col">
      <header className="flex w-full shrink-0 items-center justify-between border-b border-border px-6 py-3">
        <span className="text-xs font-medium tracking-wide">organism</span>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            className={CONTROL_CLASSES}
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            onClick={toggleTheme}
          >
            {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
          </Button>
          <Button size="icon" variant="ghost" className={CONTROL_CLASSES} title="Account">
            <User className="size-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className={CONTROL_CLASSES}
            title="Logout"
            onClick={() => { void signOut(); }}
          >
            <LogOut className="size-4" />
          </Button>
        </div>
      </header>
      <div className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
