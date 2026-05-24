import { type ReactNode } from "react";
import { AuthProvider } from "@/features/auth";
import { PaymentsUpgradeFlowProvider } from "@/features/payments";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query/queryClient";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/shared/theme/ThemeContext";

export const RootProvider = ({ children }: { children: ReactNode }) => {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <PaymentsUpgradeFlowProvider>
            <TooltipProvider>{children}</TooltipProvider>
          </PaymentsUpgradeFlowProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};
