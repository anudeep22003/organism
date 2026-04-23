import { BACKEND_URL } from "@/constants";
import { httpClient } from "@/lib/httpClient";
import { AUTH_V2_SERVICE_ENDPOINTS } from "./auth.constants";
import type { AuthUser } from "../model/auth.types";

export const authV2Api = {
  login: () => {
    window.location.assign(
      `${BACKEND_URL}${AUTH_V2_SERVICE_ENDPOINTS.LOGIN}`
    );
  },

  fetchCurrentUser: async () => {
    return await httpClient.get<AuthUser>(AUTH_V2_SERVICE_ENDPOINTS.ME);
  },

  refresh: async () => {
    await httpClient.post<void>(AUTH_V2_SERVICE_ENDPOINTS.REFRESH, {});
  },

  logout: async () => {
    await httpClient.post<void>(AUTH_V2_SERVICE_ENDPOINTS.LOGOUT, {});
  },
};
