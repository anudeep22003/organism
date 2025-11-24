import type { LoginResponse } from "../types";
import { httpClient } from "@/lib/httpClient";
import type { SignInFormData, SignUpFormData } from "../types";
import { AUTH_SERVICE_ENDPOINTS } from "../constants";

const authService = {
  fetchCurrentUser: async (accessToken: string) => {
    return await httpClient.get<Record<string, unknown>>(
      AUTH_SERVICE_ENDPOINTS.ME,
      accessToken
    );
  },

  authenticateUser: async (
    credentials: SignInFormData
  ): Promise<LoginResponse> => {
    return await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.SIGNIN,
      credentials
    );
  },

  registerUser: async (
    credentials: SignUpFormData
  ): Promise<LoginResponse> => {
    return await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.SIGNUP,
      credentials
    );
  },

  refreshAccessToken: async (accessToken: string | null) => {
    return await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.REFRESH,
      {},
      accessToken ?? undefined
    );
  },
};

export default authService;
