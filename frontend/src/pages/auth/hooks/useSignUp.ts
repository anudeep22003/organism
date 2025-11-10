import { useState, type FormEvent } from 'react';
import type { SignUpFormData, AuthFormState } from '../types';
import { validateEmail, isPasswordValid } from '../utils/validation';

export const useSignUp = (onSubmit: (data: SignUpFormData) => Promise<void>) => {
  const [formData, setFormData] = useState<SignUpFormData>({
    fullName: '',
    email: '',
    password: '',
    acceptTerms: false,
  });

  const [formState, setFormState] = useState<AuthFormState>({
    isLoading: false,
    error: null,
    validationErrors: [],
  });

  const validateForm = (): boolean => {
    const errors: { field: string; message: string }[] = [];

    if (!formData.fullName.trim()) {
      errors.push({ field: 'fullName', message: 'Full name is required' });
    }

    if (!formData.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    } else if (!validateEmail(formData.email)) {
      errors.push({ field: 'email', message: 'Invalid email format' });
    }

    if (!formData.password) {
      errors.push({ field: 'password', message: 'Password is required' });
    } else if (!isPasswordValid(formData.password)) {
      errors.push({ field: 'password', message: 'Password does not meet requirements' });
    }

    if (!formData.acceptTerms) {
      errors.push({ field: 'acceptTerms', message: 'You must accept the terms' });
    }

    setFormState(prev => ({ ...prev, validationErrors: errors }));
    return errors.length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!validateForm()) return;

    setFormState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      await onSubmit(formData);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Sign up failed';
      setFormState(prev => ({ ...prev, error: message }));
    } finally {
      setFormState(prev => ({ ...prev, isLoading: false }));
    }
  };

  const updateField = (field: keyof SignUpFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setFormState(prev => ({
      ...prev,
      validationErrors: prev.validationErrors.filter(e => e.field !== field),
    }));
  };

  const getFieldError = (field: string) =>
    formState.validationErrors.find(e => e.field === field)?.message;

  return {
    formData,
    formState,
    handleSubmit,
    updateField,
    getFieldError,
  };
};
