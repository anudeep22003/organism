import { type ReactNode } from "react";
import { SocketProvider } from "./SocketContext";
import MediaContextProvider from "./MediaContext";
import ChatProvider from "./ChatContext";
import UIProvider from "./UIContext";
import MessageMaintenanceProvider from "./MessageMaintenanceContext";
import { AuthProvider } from "@/pages/auth";
import { Provider } from "react-redux";
import { store } from "@/store";

export const RootProvider = ({ children }: { children: ReactNode }) => {
  return (
    <AuthProvider>
      <Provider store={store}>
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
      </Provider>
    </AuthProvider>
  );
};
