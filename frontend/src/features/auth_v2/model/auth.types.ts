export type AuthStatus =
  | "checking"
  | "authenticated"
  | "unauthenticated";

export interface AuthUser {
  id: string;
  email: string;
  updatedAt: string;
  fullName?: string | null;
  [key: string]: unknown;
}

export interface AuthState {
  status: AuthStatus;
  user: AuthUser | null;
}

export interface AuthContextValue extends AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}
