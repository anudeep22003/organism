import { getAxiosErrorDetails } from "@/lib/httpClient";
import { authLogger } from "@/lib/logger";
import {
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { authV2Api } from "../api/auth.api";
import { HTTP_STATUS } from "../api/auth.constants";
import { authV2Keys } from "../api/auth.query-keys";
import { meQueryOptions } from "../api/auth.queries";
import type {
  AuthContextValue,
  AuthState,
  AuthUser,
} from "./auth.types";

const AuthContext = createContext<AuthContextValue | null>(null);

const setAuthenticatedState = (
  setState: React.Dispatch<React.SetStateAction<AuthState>>,
  user: AuthUser
) => {
  setState({
    status: "authenticated",
    user,
  });
};

const setUnauthenticatedState = (
  setState: React.Dispatch<React.SetStateAction<AuthState>>
) => {
  setState({
    status: "unauthenticated",
    user: null,
  });
};

const resolveSession = async (
  queryClient: QueryClient,
  setState: React.Dispatch<React.SetStateAction<AuthState>>
) => {
  try {
    const user = await queryClient.fetchQuery(meQueryOptions());
    setAuthenticatedState(setState, user);
  } catch (error) {
    const { status } = getAxiosErrorDetails(error);
    if (status !== HTTP_STATUS.UNAUTHORIZED) {
      authLogger.error("Auth v2 bootstrap failed", error);
    }
    setUnauthenticatedState(setState);
  }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AuthState>({
    status: "checking",
    user: null,
  });
  const initializedRef = useRef(false);

  const refreshSession = useCallback(async () => {
    setState((previousState) => ({
      ...previousState,
      status: "checking",
    }));

    await resolveSession(queryClient, setState);
  }, [queryClient]);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }

    initializedRef.current = true;
    void refreshSession();
  }, [refreshSession]);

  const login = useCallback(() => {
    authV2Api.login();
  }, []);

  const logout = useCallback(async () => {
    try {
      await authV2Api.logout();
    } catch (error) {
      authLogger.error(
        "Auth v2 logout failed. Clearing local session anyway",
        error
      );
    } finally {
      queryClient.removeQueries({ queryKey: authV2Keys.all });
      setUnauthenticatedState(setState);
    }
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      isAuthenticated: state.status === "authenticated",
      isLoading: state.status === "checking",
      login,
      logout,
      refreshSession,
    }),
    [login, logout, refreshSession, state]
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
};
