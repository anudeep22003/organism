import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { PasswordInput } from './PasswordInput';
import { useSignIn } from '../hooks/useSignIn';
import type { SignInFormData } from '../types';

interface SignInFormProps {
  onSubmit: (data: SignInFormData) => Promise<void>;
}

export const SignInForm = ({ onSubmit }: SignInFormProps) => {
  const { formData, formState, handleSubmit, updateField, getFieldError } = useSignIn(onSubmit);

  const emailError = getFieldError('email');
  const passwordError = getFieldError('password');

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {formState.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{formState.error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="signin-email">Email</Label>
        <Input
          id="signin-email"
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
        <Label htmlFor="signin-password">Password</Label>
        <PasswordInput
          id="signin-password"
          autoComplete="current-password"
          placeholder="••••••••"
          value={formData.password}
          onChange={e => updateField('password', e.target.value)}
          error={!!passwordError}
          disabled={formState.isLoading}
        />
        {passwordError && <p className="text-sm text-red-500">{passwordError}</p>}
      </div>

      <Button type="submit" className="w-full" disabled={formState.isLoading}>
        {formState.isLoading ? 'Signing in...' : 'Sign In'}
      </Button>
    </form>
  );
};
