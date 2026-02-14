import { useAuth } from "./auth.context";

export const useIsAuthenticated = () => {
  return useAuth().status === "authenticated";
};

export const useIsCheckingAuth = () => {
  return useAuth().status === "checking";
};
