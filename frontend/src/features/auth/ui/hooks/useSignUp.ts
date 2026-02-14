import { useState, type FormEvent } from "react";
import { AUTH_FIELDS } from "../../api/auth.constants";
import type {
  AuthFormState,
  SignUpInput,
  ValidationError,
} from "../../model/auth.types";
import { isPasswordValid, validateEmail } from "../utils/validation";

export const useSignUp = (
  onSubmit: (data: SignUpInput) => Promise<void>
) => {
  const [formData, setFormData] = useState<SignUpInput>({
    fullName: "",
    email: "",
    password: "",
    acceptTerms: false,
  });

  const [formState, setFormState] = useState<AuthFormState>({
    isLoading: false,
    error: null,
    validationErrors: [],
  });

  const validateForm = (): boolean => {
    const errors: ValidationError[] = [];

    if (!formData.fullName.trim()) {
      errors.push({
        field: AUTH_FIELDS.FULL_NAME,
        message: "Full name is required",
      });
    }

    if (!formData.email) {
      errors.push({
        field: AUTH_FIELDS.EMAIL,
        message: "Email is required",
      });
    } else if (!validateEmail(formData.email)) {
      errors.push({
        field: AUTH_FIELDS.EMAIL,
        message: "Invalid email format",
      });
    }

    if (!formData.password) {
      errors.push({
        field: AUTH_FIELDS.PASSWORD,
        message: "Password is required",
      });
    } else if (!isPasswordValid(formData.password)) {
      errors.push({
        field: AUTH_FIELDS.PASSWORD,
        message: "Password does not meet requirements",
      });
    }

    if (!formData.acceptTerms) {
      errors.push({
        field: AUTH_FIELDS.ACCEPT_TERMS,
        message: "You must accept the terms",
      });
    }

    setFormState((prev) => ({ ...prev, validationErrors: errors }));
    return errors.length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateForm()) return;

    setFormState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      await onSubmit(formData);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Sign up failed";
      setFormState((prev) => ({ ...prev, error: message }));
    } finally {
      setFormState((prev) => ({ ...prev, isLoading: false }));
    }
  };

  const updateField = (
    field: keyof SignUpInput,
    value: string | boolean
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));

    const fieldMap: Record<keyof SignUpInput, string> = {
      fullName: AUTH_FIELDS.FULL_NAME,
      email: AUTH_FIELDS.EMAIL,
      password: AUTH_FIELDS.PASSWORD,
      acceptTerms: AUTH_FIELDS.ACCEPT_TERMS,
    };

    setFormState((prev) => ({
      ...prev,
      validationErrors: prev.validationErrors.filter(
        (error) => error.field !== fieldMap[field]
      ),
    }));
  };

  const getFieldError = (field: keyof SignUpInput) =>
    formState.validationErrors.find((error) => error.field === field)
      ?.message;

  return {
    formData,
    formState,
    handleSubmit,
    updateField,
    getFieldError,
  };
};
