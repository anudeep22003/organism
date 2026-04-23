import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { SignInInput } from "../../model/auth.types";
import { useSignIn } from "../hooks/useSignIn";
import { PasswordInput } from "./PasswordInput";

interface SignInFormProps {
  onSubmit: (data: SignInInput) => Promise<void>;
}

export const SignInForm = ({ onSubmit }: SignInFormProps) => {
  const {
    formData,
    formState,
    handleSubmit,
    updateField,
    getFieldError,
  } = useSignIn(onSubmit);

  const emailError = getFieldError("email");
  const passwordError = getFieldError("password");

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
          onChange={(event) =>
            updateField("email", event.target.value)
          }
          className={
            emailError ? "border-red-500 focus-visible:ring-red-500" : ""
          }
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
          onChange={(event) =>
            updateField("password", event.target.value)
          }
          error={Boolean(passwordError)}
          disabled={formState.isLoading}
        />
        {passwordError && (
          <p className="text-sm text-red-500">{passwordError}</p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={formState.isLoading}>
        {formState.isLoading ? "Signing in..." : "Sign In"}
      </Button>
    </form>
  );
};
