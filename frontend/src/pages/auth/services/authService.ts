import type { LoginResponse, LogoutResponse, User } from "../types";
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

  logoutUserAndClearAccessToken: async (): Promise<void> => {
    const response = await httpClient.post<LogoutResponse>(
      AUTH_SERVICE_ENDPOINTS.LOGOUT,
      {}
    );
    authLogger.debug("Logout user response: ", response);
    if (response.message !== "LOGGED_OUT") {
      throw new Error("Failed to logout user");
    }
    httpClient.clearSession();
    authLogger.debug("Logged out user");
  },
};

export default authService;
