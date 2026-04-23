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
import { useSignInMutation, useSignOutMutation, useSignUpMutation } from "../api/auth.mutations";
import { authKeys } from "../api/auth.query-keys";
import { meQueryOptions } from "../api/auth.queries";
import { HTTP_STATUS } from "../api/auth.constants";
import { tokenStore } from "../session/token.store";
import type {
  AuthContextValue,
  AuthState,
  SignInInput,
  SignUpInput,
  User,
} from "./auth.types";

const AuthContext = createContext<AuthContextValue | null>(null);

const getCurrentAccessToken = () => tokenStore.get();

const setAuthenticatedState = (
  setState: React.Dispatch<React.SetStateAction<AuthState>>,
  user: User,
  accessToken: string | null
) => {
  setState({
    status: "authenticated",
    user,
    accessToken,
  });
};

const setUnauthenticatedState = (
  setState: React.Dispatch<React.SetStateAction<AuthState>>
) => {
  setState({
    status: "unauthenticated",
    user: null,
    accessToken: null,
  });
};

const resolveSession = async (
  queryClient: QueryClient,
  setState: React.Dispatch<React.SetStateAction<AuthState>>
) => {
  try {
    const user = await queryClient.fetchQuery(meQueryOptions());
    setAuthenticatedState(setState, user, getCurrentAccessToken());
  } catch (err) {
    const { status } = getAxiosErrorDetails(err);
    if (status !== HTTP_STATUS.UNAUTHORIZED) {
      authLogger.error("Auth bootstrap failed:", err);
    }
    setUnauthenticatedState(setState);
  }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const queryClient = useQueryClient();
  const signInMutation = useSignInMutation();
  const signUpMutation = useSignUpMutation();
  const signOutMutation = useSignOutMutation();

  const [state, setState] = useState<AuthState>({
    status: "checking",
    accessToken: getCurrentAccessToken(),
    user: null,
  });

  const initializedRef = useRef(false);

  useEffect(() => {
    return tokenStore.subscribe((accessToken) => {
      setState((previousState) => ({
        ...previousState,
        accessToken,
      }));
    });
  }, []);

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

  useEffect(() => {
    if (
      state.status === "authenticated" &&
      state.accessToken === null
    ) {
      setUnauthenticatedState(setState);
      queryClient.removeQueries({ queryKey: authKeys.me() });
    }
  }, [queryClient, state.accessToken, state.status]);

  const signIn = useCallback(
    async (input: SignInInput) => {
      const response = await signInMutation.mutateAsync(input);
      tokenStore.set(response.accessToken);
      queryClient.setQueryData(authKeys.me(), response.user);
      setAuthenticatedState(setState, response.user, response.accessToken);
    },
    [queryClient, signInMutation]
  );

  const signUp = useCallback(
    async (input: SignUpInput) => {
      const response = await signUpMutation.mutateAsync(input);
      tokenStore.set(response.accessToken);
      queryClient.setQueryData(authKeys.me(), response.user);
      setAuthenticatedState(setState, response.user, response.accessToken);
    },
    [queryClient, signUpMutation]
  );

  const signOut = useCallback(async () => {
    try {
      await signOutMutation.mutateAsync();
    } catch (err) {
      authLogger.error("Logout failed. Clearing local session anyway", err);
    } finally {
      await tokenStore.clear();
      queryClient.removeQueries({ queryKey: authKeys.all });
      setUnauthenticatedState(setState);
    }
  }, [queryClient, signOutMutation]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      signIn,
      signUp,
      signOut,
      refreshSession,
    }),
    [refreshSession, signIn, signOut, signUp, state]
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
