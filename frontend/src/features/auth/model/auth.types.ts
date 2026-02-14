export type AuthStatus =
  | "checking"
  | "authenticated"
  | "unauthenticated";

export interface SignInInput {
  email: string;
  password: string;
}

export interface SignUpInput {
  fullName: string;
  email: string;
  password: string;
  acceptTerms: boolean;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface PasswordRequirement {
  label: string;
  met: boolean;
}

export interface PasswordValidation {
  isValid: boolean;
  requirements: PasswordRequirement[];
  strength: "weak" | "medium" | "strong";
}

export interface AuthFormState {
  isLoading: boolean;
  error: string | null;
  validationErrors: ValidationError[];
}

export interface User {
  id: string;
  email: string;
  fullName: string;
}

export interface LoginResponse {
  accessToken: string;
  user: User;
}

export interface LogoutResponse {
  message: "LOGGED_OUT";
}

export interface AuthState {
  status: AuthStatus;
  accessToken: string | null;
  user: User | null;
}

export interface AuthContextValue extends AuthState {
  signIn: (input: SignInInput) => Promise<void>;
  signUp: (input: SignUpInput) => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
}
