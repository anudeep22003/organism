import { type ReactNode } from "react";
import { SocketProvider } from "./SocketContext";
import MediaContextProvider from "./MediaContext";
import ChatProvider from "./ChatContext";
import UIProvider from "./UIContext";
import MessageMaintenanceProvider from "./MessageMaintenanceContext";
import { AuthProvider } from "@/pages/auth";

export const RootProvider = ({ children }: { children: ReactNode }) => {
  return (
    <AuthProvider>
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
    </AuthProvider>
  );
};
