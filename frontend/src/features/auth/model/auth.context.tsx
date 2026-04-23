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

/*
State machine overview:

- `checking` means the provider is resolving session truth from the backend.
- `authenticated` means `/api/auth/me` returned a user.
- `unauthenticated` means bootstrap or refresh settled with no valid session.

The provider owns app-facing auth state, but it does not own transport rules.
`httpClient` handles cookie refresh and CSRF, while this provider translates
the backend session contract into a simple React state machine the rest of the
app can consume through `useAuth()`.
*/
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
  /*
  This is the only place where auth state is derived from backend truth.
  We fetch `/api/auth/me`; if that succeeds we are authenticated, and if it
  fails with 401 after any transport-level refresh attempt we are not.
  */
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
    /*
    Public refresh flow:

    1. move back to `checking`
    2. ask the backend who the current user is
    3. settle to `authenticated` or `unauthenticated`

    Callers do not need to think about refresh cookies here; `httpClient`
    already retries `/me` through `/api/auth/refresh` when that is possible.
    */
    setState((previousState) => ({
      ...previousState,
      status: "checking",
    }));

    await resolveSession(queryClient, setState);
  }, [queryClient]);

  useEffect(() => {
    /*
    Bootstrap runs once when the provider mounts. Guards read this provider,
    so keeping bootstrap centralized here prevents route-level auth effects
    from spreading across the app.
    */
    if (initializedRef.current) {
      return;
    }

    initializedRef.current = true;
    void refreshSession();
  }, [refreshSession]);

  const login = useCallback(() => {
    authApi.login();
  }, []);

  const logout = useCallback(async () => {
    try {
      /*
      Logout is best-effort at the network boundary and deterministic locally:
      we try to revoke the server session, but we always clear local auth state
      so the app never stays "signed in" because logout transport failed.
      */
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
