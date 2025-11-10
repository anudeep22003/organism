import { AlertCircle, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { PasswordInput } from './PasswordInput';
import { useSignUp } from '../hooks/useSignUp';
import { usePasswordValidation } from '../hooks/usePasswordValidation';
import type { SignUpFormData } from '../types';
import { cn } from '@/lib/utils';

interface SignUpFormProps {
  onSubmit: (data: SignUpFormData) => Promise<void>;
}

export const SignUpForm = ({ onSubmit }: SignUpFormProps) => {
  const { formData, formState, handleSubmit, updateField, getFieldError } = useSignUp(onSubmit);
  const passwordValidation = usePasswordValidation(formData.password);

  const fullNameError = getFieldError('fullName');
  const emailError = getFieldError('email');
  const passwordError = getFieldError('password');
  const termsError = getFieldError('acceptTerms');

  const strengthColors = {
    weak: 'bg-red-500',
    medium: 'bg-yellow-500',
    strong: 'bg-green-500',
  };

  const strengthWidth = {
    weak: 'w-1/3',
    medium: 'w-2/3',
    strong: 'w-full',
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {formState.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{formState.error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="signup-fullname">Full Name</Label>
        <Input
          id="signup-fullname"
          type="text"
          autoComplete="name"
          placeholder="John Doe"
          value={formData.fullName}
          onChange={e => updateField('fullName', e.target.value)}
          className={fullNameError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          disabled={formState.isLoading}
        />
        {fullNameError && <p className="text-sm text-red-500">{fullNameError}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="signup-email">Email</Label>
        <Input
          id="signup-email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={formData.email}
          onChange={e => updateField('email', e.target.value)}
          className={emailError ? 'border-red-500 focus-visible:ring-red-500' : ''}
          disabled={formState.isLoading}
        />
        {emailError && <p className="text-sm text-red-500">{emailError}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="signup-password">Password</Label>
        <PasswordInput
          id="signup-password"
          autoComplete="new-password"
          placeholder="••••••••"
          value={formData.password}
          onChange={e => updateField('password', e.target.value)}
          error={!!passwordError}
          disabled={formState.isLoading}
        />

        {formData.password && (
          <>
            <div className="space-y-1">
              <div className="h-1 w-full bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full transition-all duration-300',
                    strengthColors[passwordValidation.strength],
                    strengthWidth[passwordValidation.strength]
                  )}
                />
              </div>
              <p className="text-xs text-gray-500 capitalize">
                Password strength: {passwordValidation.strength}
              </p>
            </div>

            <ul className="space-y-1">
              {passwordValidation.requirements.map((req, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  {req.met ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <X className="h-4 w-4 text-gray-400" />
                  )}
                  <span className={req.met ? 'text-green-500' : 'text-gray-500'}>
                    {req.label}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}

        {passwordError && <p className="text-sm text-red-500">{passwordError}</p>}
      </div>

      <div className="flex items-center space-x-2">
        <input
          id="signup-terms"
          type="checkbox"
          checked={formData.acceptTerms}
          onChange={e => updateField('acceptTerms', e.target.checked)}
          className="h-4 w-4 rounded border-gray-300"
          disabled={formState.isLoading}
        />
        <Label htmlFor="signup-terms" className="text-sm font-normal cursor-pointer">
          I accept the terms and conditions
        </Label>
      </div>
      {termsError && <p className="text-sm text-red-500">{termsError}</p>}

      <Button type="submit" className="w-full" disabled={formState.isLoading}>
        {formState.isLoading ? 'Creating account...' : 'Sign Up'}
      </Button>
    </form>
  );
};
