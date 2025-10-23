import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

interface UIContextType {
  showGenerative: boolean;
  setShowGenerative: (showGenerative: boolean) => void;
}

const UIContext = createContext<UIContextType | null>(null);

const UIProvider = ({ children }: { children: ReactNode }) => {
  const [showGenerative, setShowGenerative] = useState(false);

  return (
    <UIContext.Provider value={{ showGenerative, setShowGenerative }}>
      {children}
    </UIContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useUIContext = () => {
  const uiContext = useContext(UIContext);
  if (!uiContext) {
    throw new Error("useUIContext must be used within a UIProvider");
  }
  return uiContext;
};

export default UIProvider;
