import type { LoginResponse } from "..";
import { httpClient } from "@/lib/httpClient";
import { AxiosError } from "axios";
import { authLogger } from "@/lib/logger";
import type { SignInFormData, SignUpFormData } from "../types";

const useAuthEntry = () => {
  const doesRefreshTokenExistInCookies = () => {
    authLogger.debug("cookies: ", document.cookie);
    const cookies = document.cookie.split(";");
    const refreshToken = cookies.find((cookie) =>
      cookie.includes("refresh_token")
    );
    authLogger.debug("refreshToken: ", refreshToken);
    return refreshToken ? true : false;
  };

  const getUser = async (accessToken: string) => {
    try {
      const response = await httpClient.get<LoginResponse>(
        "api/auth/me",
        accessToken
      );
      authLogger.debug("response", response);
    } catch (err) {
      authLogger.debug("error", err);
      if (err instanceof AxiosError) {
        authLogger.debug("Axios error:", err);
        const statusCode = err.response?.status ?? 500;
        authLogger.debug("statusCode", statusCode);
      }
    }
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

  return { getUser, doesRefreshTokenExistInCookies, signIn, signUp };
};

export default useAuthEntry;
