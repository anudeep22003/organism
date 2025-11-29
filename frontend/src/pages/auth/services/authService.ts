import type { LoginResponse, User } from "../types";
import { httpClient } from "@/lib/httpClient";
import type { SignInFormData, SignUpFormData } from "../types";
import { AUTH_SERVICE_ENDPOINTS } from "../constants";
import { authLogger } from "@/lib/logger";

const authService = {
  fetchCurrentUser: async () => {
    return await httpClient.get<User>(AUTH_SERVICE_ENDPOINTS.ME);
  },

  authenticateUserAndSetAccessToken: async (
    credentials: SignInFormData
  ): Promise<void> => {
    const response = await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.SIGNIN,
      credentials
    );
    httpClient.setAccessToken(response.accessToken);
    authLogger.debug(
      "Authenticated new user (signin), and set the access token. Response: ",
      response
    );
  },

  registerUserAndSetAccessToken: async (
    credentials: SignUpFormData
  ): Promise<void> => {
    const response = await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.SIGNUP,
      credentials
    );
    httpClient.setAccessToken(response.accessToken);
    authLogger.debug(
      "Registered new user (signup), and set the access token. Response: ",
      response
    );
  },

  refreshAndSetAccessToken: async (
    accessToken: string | null
  ): Promise<void> => {
    const response = await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.REFRESH,
      {},
      accessToken ?? undefined
    );
    httpClient.setAccessToken(response.accessToken);
    authLogger.debug(
      "Refreshed access token (refresh), and set the access token. Response: ",
      response
    );
  },
};

export default authService;
