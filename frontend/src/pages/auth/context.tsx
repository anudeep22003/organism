import { httpClient } from "@/lib/httpClient";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { LoginResponse } from ".";
import { AxiosError } from "axios";
import { useNavigate } from "react-router";
import useAuthEntry from "./hooks/useAuthEntry";

interface AuthContextType {
  accessToken: string | null;
  setAccessToken: (accessToken: string | null) => void;
  statusCode: number | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [statusCode, setStatusCode] = useState<number | null>(null);
  const { getUser } = useAuthEntry();

  useEffect(() => {
    if (!accessToken) console.log("no access token");
    return;
    getUser(accessToken);
    // const handleRefreshAccessToken = async () => {
    //   try {
    //     const response = await httpClient.post<LoginResponse>(
    //       "/api/auth/refresh",
    //       {},
    //       accessToken ?? undefined
    //     );
    //     setAccessToken(response.accessToken ?? null);
    //     console.log("refreshed effect completed", response);
    //   } catch (err) {
    //     if (err instanceof AxiosError) {
    //       console.log("Axios error:", err);
    //       const statusCode = err.response?.status;
    //       setStatusCode(statusCode ?? null);
    //     }
    //     setStatusCode(500);
    //   }
    // };
    // handleRefreshAccessToken();
  }, [accessToken, getUser]);

  return (
    <AuthContext.Provider
      value={{ accessToken, setAccessToken, statusCode }}
    >
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
