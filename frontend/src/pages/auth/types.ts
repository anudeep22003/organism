export interface SignInFormData {
  email: string;
  password: string;
}

export interface SignUpFormData {
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
