import { useState, type FormEvent } from "react";
import { AUTH_FIELDS } from "../../api/auth.constants";
import type {
  AuthFormState,
  SignInInput,
  ValidationError,
} from "../../model/auth.types";
import { validateEmail } from "../utils/validation";

export const useSignIn = (
  onSubmit: (data: SignInInput) => Promise<void>
) => {
  const [formData, setFormData] = useState<SignInInput>({
    email: "",
    password: "",
  });

  const [formState, setFormState] = useState<AuthFormState>({
    isLoading: false,
    error: null,
    validationErrors: [],
  });

  const validateForm = (): boolean => {
    const errors: ValidationError[] = [];

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
        error instanceof Error ? error.message : "Sign in failed";
      setFormState((prev) => ({ ...prev, error: message }));
    } finally {
      setFormState((prev) => ({ ...prev, isLoading: false }));
    }
  };

  const updateField = (field: keyof SignInInput, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setFormState((prev) => ({
      ...prev,
      validationErrors: prev.validationErrors.filter(
        (error) => error.field !== field
      ),
    }));
  };

  const getFieldError = (field: keyof SignInInput) =>
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
