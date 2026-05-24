import { useTheme } from "@/shared/theme/ThemeContext";
import { useAuth } from "@/features/auth";
import { Outlet, useLocation, useNavigate } from "react-router";

export default function StoriesLayout() {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isDark = theme === "dark";
  const isAccountRoute = location.pathname.startsWith("/account");
  const isStoriesRoute = location.pathname.startsWith("/stories");
  const isPaymentsRoute = location.pathname.startsWith("/payments");

  return (
    <div className="flex h-screen flex-col">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-1.5">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Organism</span>
          <div className="h-2.5 w-px bg-border" />
          <button
            onClick={() => void navigate("/stories")}
            className={`text-[10px] ${
              isStoriesRoute
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Stories
          </button>
          <button
            onClick={() => void navigate("/payments")}
            className={`text-[10px] ${
              isPaymentsRoute
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Payments
          </button>
          <button
            onClick={() => void navigate("/account")}
            className={`text-[10px] ${
              isAccountRoute
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Account
          </button>
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
            onClick={() => {
              void logout();
            }}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            Sign out
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
