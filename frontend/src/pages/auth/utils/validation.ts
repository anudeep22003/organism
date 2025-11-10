import type { PasswordRequirement } from '../types';

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const getPasswordRequirements = (password: string): PasswordRequirement[] => {
  return [
    {
      label: 'At least 8 characters',
      met: password.length >= 8,
    },
    {
      label: 'One uppercase letter',
      met: /[A-Z]/.test(password),
    },
    {
      label: 'One lowercase letter',
      met: /[a-z]/.test(password),
    },
    {
      label: 'One number',
      met: /\d/.test(password),
    },
    {
      label: 'One special character',
      met: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    },
  ];
};

export const calculatePasswordStrength = (
  requirements: PasswordRequirement[]
): 'weak' | 'medium' | 'strong' => {
  const metCount = requirements.filter(req => req.met).length;

  if (metCount <= 2) return 'weak';
  if (metCount <= 4) return 'medium';
  return 'strong';
};

export const isPasswordValid = (password: string): boolean => {
  const requirements = getPasswordRequirements(password);
  return requirements.every(req => req.met);
};
