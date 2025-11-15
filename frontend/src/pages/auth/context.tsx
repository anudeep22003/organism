import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

interface AuthContextType {
  accessToken: string | null;
  setAccessToken: (accessToken: string | null) => void;
  checkingAuth: boolean;
  setCheckingAuth: (checkingAuth: boolean) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  return (
    <AuthContext.Provider value={{ accessToken, setAccessToken, checkingAuth, setCheckingAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuthContext = () => {
  const authContext = useContext(AuthContext);
  if (!authContext) {
    throw new Error(
      "useAuthContext must be used within a AuthProvider"
    );
  }
  return authContext;
};

export default AuthProvider;
