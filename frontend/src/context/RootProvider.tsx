import { type ReactNode } from "react";
import { SocketProvider } from "./SocketContext";
import MediaContextProvider from "./MediaContext";
import ChatProvider from "./ChatContext";
import UIProvider from "./UIContext";
import MessageMaintenanceProvider from "./MessageMaintenanceContext";
import { AuthProvider } from "@/features/auth";
import { Provider } from "react-redux";
import { store } from "@/store";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/shared/query/queryClient";
import { TooltipProvider } from "@/components/ui/tooltip";

export const RootProvider = ({ children }: { children: ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Provider store={store}>
          <TooltipProvider>
            <SocketProvider>
              <MediaContextProvider>
                <UIProvider>
                  <ChatProvider>
                    <MessageMaintenanceProvider>
                      {children}
                    </MessageMaintenanceProvider>
                  </ChatProvider>
                </UIProvider>
              </MediaContextProvider>
            </SocketProvider>
          </TooltipProvider>
        </Provider>
      </AuthProvider>
    </QueryClientProvider>
  );
};
