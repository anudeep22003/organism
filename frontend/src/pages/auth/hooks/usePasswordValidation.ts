import { useMemo } from 'react';
import type { PasswordValidation } from '../types';
import {
  getPasswordRequirements,
  calculatePasswordStrength,
  isPasswordValid,
} from '../utils/validation';

export const usePasswordValidation = (password: string): PasswordValidation => {
  return useMemo(() => {
    const requirements = getPasswordRequirements(password);
    const strength = calculatePasswordStrength(requirements);
    const isValid = isPasswordValid(password);

    return {
      isValid,
      requirements,
      strength,
    };
  }, [password]);
};
