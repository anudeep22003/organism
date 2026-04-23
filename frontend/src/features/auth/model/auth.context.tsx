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
import { authApi } from "../api/auth.api";
import { HTTP_STATUS } from "../api/auth.constants";
import { authKeys } from "../api/auth.query-keys";
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
      authLogger.error("Auth bootstrap failed", error);
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
    // mark the auth state as checking
    setState((previousState) => ({
      ...previousState,
      status: "checking",
    }));

    // tries to hit the me endpoint, and loads the user or if unauthorized, marks that in the central auth state
    // the httpClient takes care of refreshing if required
    await resolveSession(queryClient, setState);
  }, [queryClient]);

  useEffect(() => {
    // if the auth provider has already been initialized, don't do anything
    if (initializedRef.current) {
      return;
    }

    // set the initialized flag to true and refresh the session
    initializedRef.current = true;
    void refreshSession();
  }, [refreshSession]);

  const login = useCallback(() => {
    authApi.login();
  }, []);

  const logout = useCallback(async () => {
    try {
      // tries to hit the logout endpoint, and clears the local session state
      await authApi.logout();
    } catch (error) {
      authLogger.error(
        "Auth logout failed. Clearing local session anyway",
        error
      );
    } finally {
      queryClient.removeQueries({ queryKey: authKeys.all });
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
