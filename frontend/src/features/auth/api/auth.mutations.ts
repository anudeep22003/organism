import { useMutation } from "@tanstack/react-query";
import { authApi } from "./auth.api";

export const useSignInMutation = () => {
  return useMutation({
    mutationFn: authApi.signIn,
  });
};

export const useSignUpMutation = () => {
  return useMutation({
    mutationFn: authApi.signUp,
  });
};

export const useSignOutMutation = () => {
  return useMutation({
    mutationFn: authApi.logout,
  });
};
