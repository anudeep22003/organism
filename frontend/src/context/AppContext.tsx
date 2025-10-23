import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { useMessageStore } from "@/store/useMessageStore";
import { SocketProvider } from "./SocketContext";
import MediaContextProvider from "./MediaContext";
import ChatProvider from "./ChatContext";

interface AppContextType {
  showGenerative: boolean;
  setShowGenerative: (showGenerative: boolean) => void;
}

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [showGenerative, setShowGenerative] = useState(false);
  // Get store functions

  const { clearOldMessages } = useMessageStore();
  // Periodic cleanup of old messages
  useEffect(() => {
    const interval = setInterval(() => {
      clearOldMessages();
    }, 60000); // Clear old messages every minute

    return () => clearInterval(interval);
  }, [clearOldMessages]);

  return (
    <AppContext.Provider
      value={{
        showGenerative,
        setShowGenerative,
      }}
    >
      <SocketProvider>
        <MediaContextProvider>
          <ChatProvider>{children}</ChatProvider>
        </MediaContextProvider>
      </SocketProvider>
    </AppContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
};
