import { httpClient } from "@/lib/httpClient";
import { AUTH_SERVICE_ENDPOINTS } from "./auth.constants";
import type {
  LoginResponse,
  LogoutResponse,
  SignInInput,
  SignUpInput,
  User,
} from "../model/auth.types";

export const authApi = {
  fetchCurrentUser: async () => {
    return await httpClient.get<User>(AUTH_SERVICE_ENDPOINTS.ME);
  },

  signIn: async (credentials: SignInInput) => {
    return await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.SIGNIN,
      credentials
    );
  },

  signUp: async (credentials: SignUpInput) => {
    return await httpClient.post<LoginResponse>(
      AUTH_SERVICE_ENDPOINTS.SIGNUP,
      credentials
    );
  },

  logout: async () => {
    return await httpClient.post<LogoutResponse>(
      AUTH_SERVICE_ENDPOINTS.LOGOUT,
      {}
    );
  },
};
