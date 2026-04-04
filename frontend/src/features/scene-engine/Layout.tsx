import { useTheme } from "@/context/ThemeContext";
import { Outlet } from "react-router";
import { useAuth } from "../auth/model/auth.context";

export default function SceneEngineLayout() {
  const { signOut } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className="flex h-screen flex-col">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-1.5">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Organism</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            {isDark ? "Light" : "Dark"}
          </button>
          <div className="h-2.5 w-px bg-border" />
          <button
            onClick={() => { void signOut(); }}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            Sign out
          </button>
          <div className="h-2.5 w-px bg-border" />
          <button className="flex h-5 w-5 items-center justify-center border border-border text-[10px] text-muted-foreground hover:bg-muted/40">
            A
          </button>
        </div>
      </div>
      <div className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
