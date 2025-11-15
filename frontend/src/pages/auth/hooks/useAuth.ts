import type { LoginResponse } from "..";
import { httpClient } from "@/lib/httpClient";
import type { SignInFormData, SignUpFormData } from "../types";

const useAuthEntry = () => {
  const getUser = async (accessToken: string) => {
    return await httpClient.get<Record<string, unknown>>(
      "/api/auth/me",
      accessToken
    );
  };

  const signIn = async (
    credentials: SignInFormData
  ): Promise<LoginResponse> => {
    return await httpClient.post<LoginResponse>(
      "/api/auth/signin",
      credentials
    );
  };

  const signUp = async (
    credentials: SignUpFormData
  ): Promise<LoginResponse> => {
    return await httpClient.post<LoginResponse>(
      "/api/auth/signup",
      credentials
    );
  };

  const getRefreshedAccessToken = async () => {
    return await httpClient.post<LoginResponse>(
      "/api/auth/refresh_access_token",
      {}
    );
  };

  return { getUser, signIn, signUp, getRefreshedAccessToken };
};

export default useAuthEntry;
