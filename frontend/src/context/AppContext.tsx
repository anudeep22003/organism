import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { useMessageStore } from "@/store/useMessageStore";
import type { MediaManager } from "@/audio/services/mediaManager";
import useAudio from "@/audio/hooks/useAudio";
import { SocketProvider } from "./SocketContext";
import { ChatProvider } from "./ChatContext";

interface AppContextType {
  inputText: string;
  setInputText: (
    inputText: string | ((prevText: string) => string)
  ) => void;
  showGenerative: boolean;
  setShowGenerative: (showGenerative: boolean) => void;
  mediaManager: MediaManager | null;
}

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [inputText, setInputText] = useState("");
  const [showGenerative, setShowGenerative] = useState(false);
  const { mediaManager } = useAudio();
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
        inputText,
        setInputText,
        showGenerative,
        setShowGenerative,
        mediaManager,
      }}
    >
      <SocketProvider>
        <ChatProvider>{children}</ChatProvider>
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
