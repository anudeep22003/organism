import { type ReactNode } from "react";
import { SocketProvider } from "./SocketContext";
import MediaContextProvider from "./MediaContext";
import ChatProvider from "./ChatContext";
import UIProvider from "./UIContext";
import MessageMaintenanceProvider from "./MessageMaintenanceContext";

export const RootProvider = ({ children }: { children: ReactNode }) => {
  return (
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
  );
};
