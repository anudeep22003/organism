import { type ReactNode } from "react";
import { ThemeProvider } from "./ThemeContext";
import { AuthProvider } from "@/features/auth";
import { Provider } from "react-redux";
import { store } from "@/store";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/shared/query/queryClient";
import { TooltipProvider } from "@/components/ui/tooltip";

export const RootProvider = ({ children }: { children: ReactNode }) => {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Provider store={store}>
            <TooltipProvider>{children}</TooltipProvider>
          </Provider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};
