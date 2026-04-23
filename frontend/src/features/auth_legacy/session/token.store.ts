import { httpClient } from "@/lib/httpClient";

export const tokenStore = {
  get: () => httpClient.getAccessToken(),
  set: (token: string) => httpClient.setAccessToken(token),
  clear: () => httpClient.clearSession(),
  subscribe: (listener: (token: string | null) => void) =>
    httpClient.subscribeToAccessToken(listener),
};
