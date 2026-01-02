import { BACKEND_URL } from "@/constants";
import {
  ACCESS_TOKEN_EXPIRY_TIME,
  AUTH_SERVICE_ENDPOINTS,
  HTTP_STATUS,
} from "@/pages/auth/constants";
import { type LoginResponse } from "@/pages/auth/types";
import axios, { AxiosError, type AxiosInstance } from "axios";
import { apiLogger, authLogger } from "./logger";

class HttpClient {
  private static instance: HttpClient;
  private axiosInstance: AxiosInstance;
  private accessToken: string | null = null;
  private updateReactStateCallback?: (token: string | null) => void;
  private refreshTimer: NodeJS.Timeout | null = null;
  private isRefreshing: boolean = false;

  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: BACKEND_URL,
      withCredentials: true,
      timeout: 30000, // 30 seconds timeout
    });

    this.setupInterceptors();
  }

  public setReactStateUpdateFn(
    callback: (token: string | null) => void
  ) {
    this.updateReactStateCallback = callback;
  }

  public async post<T = unknown>(
    url: string,
    data?: unknown
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data, {});
      return response.data;
    } catch (error) {
      apiLogger.error("HTTP Request Error", { error });
      throw error;
    }
  }

  public async get<T = unknown>(url: string): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(url, {});
      return response.data;
    } catch (error) {
      apiLogger.error("HTTP Request Error", { error });
      throw error;
    }
  }

  public static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }

  public setAccessToken(token: string) {
    if (!token) {
      throw new Error("Null access token being tried to set");
    }

    // Clear any existing timer
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    this.accessToken = token;

    // Start new refresh timer
    this.refreshTimer = setTimeout(() => {
      this.refreshAccessToken();
    }, ACCESS_TOKEN_EXPIRY_TIME);

    if (this.updateReactStateCallback) {
      this.updateReactStateCallback(token);
    }
  }

  public async refreshAccessToken(): Promise<void> {
    if (this.isRefreshing) {
      authLogger.debug("Already refreshing access token");
      return;
    }

    this.isRefreshing = true;

    try {
      const { accessToken: newAccessToken } =
        await this.post<LoginResponse>(
          AUTH_SERVICE_ENDPOINTS.REFRESH,
          {}
        );
      this.setAccessToken(newAccessToken);
    } catch (err) {
      throw new Error(`Error refreshing Access token, ${err}`);
    } finally {
      this.isRefreshing = false;
    }
  }

  public async clearSession(): Promise<void> {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    this.refreshTimer = null;

    // clear the access token (dont call setAccessToken)
    this.accessToken = null;

    // Notify react
    if (this.updateReactStateCallback) {
      this.updateReactStateCallback(null);
    }

    authLogger.debug("Cleared session");
  }

  private shouldAttemptRefresh(error: AxiosError): boolean {
    // Dont try to refresh if:
    // 1. The request itself is a refresh request
    // 2. Already refreshing (prevents concurrent refresh attempts)
    // 3. The request is a logout request
    // 4. The request is authorized
    const isRefreshRequest = error.config?.url?.includes(
      AUTH_SERVICE_ENDPOINTS.REFRESH
    );
    const isLogoutRequest = error.config?.url?.includes(
      AUTH_SERVICE_ENDPOINTS.LOGOUT
    );
    const isAuthorized =
      error.response?.status !== HTTP_STATUS.UNAUTHORIZED;
    return (
      !isAuthorized &&
      !isRefreshRequest &&
      !this.isRefreshing &&
      !isLogoutRequest
    );
  }

  public async *streamPost<T = unknown>(
    data?: unknown
  ): AsyncGenerator<T> {
    const url = `${BACKEND_URL}/api/comic-builder/story`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.accessToken && {
          Authorization: `Bearer ${this.accessToken}`,
        }),
      },
      body: JSON.stringify(data),
      credentials: "include",
    });

    // Handle 401 - attempt refresh and retry
    if (
      response.status === HTTP_STATUS.UNAUTHORIZED &&
      !this.isRefreshing
    ) {
      await this.refreshAccessToken();

      // Retry the reqyest
      yield* this.streamPost(data);
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No readable stream available");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? ""; // keep incomplete line in buffer

      for (const line of lines) {
        yield JSON.parse(line) as T;
      }
    }

    // yield the last line if it exists
    if (buffer.trim()) {
      yield JSON.parse(buffer) as T;
    }
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // set auth header globally or set it to undefined
        config.headers.Authorization = this.accessToken
          ? `Bearer ${this.accessToken}`
          : undefined;

        return config;
      },
      (error) => {
        apiLogger.error("HTTP Request Error", { error });
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.axiosInstance.interceptors.response.use(
      (response) => {
        apiLogger.debug("HTTP Response", {
          status: response.status,
          url: response.config.url,
        });
        return response;
      },
      async (error) => {
        // storing the original request to reattempt
        const originalRequest = error.config;
        if (this.shouldAttemptRefresh(error)) {
          authLogger.debug(
            "No accessToken or unauthorized meaning token expired. Will attempt refresh",
            error,
            "current accessToken = ",
            this.accessToken
          );
          try {
            // the accessToken is refreshed and public instance is updated
            await this.refreshAccessToken();

            // Retry the failed request
            authLogger.debug("Reattempting the failed request.");
            return this.axiosInstance.request(originalRequest);
          } catch (refreshError) {
            // add an onAuthFailure callback here to let react know of the failure
            authLogger.debug("Refresh failed", refreshError);
            // Clear the session to reset the access token
            this.clearSession();
          }
          return Promise.reject(error);
        }
      }
    );
  }

  public getTranscribeApi() {
    return {
      whisper: (formData: FormData) =>
        this.axiosInstance.post<string>(
          "/api/transcribe/whisper",
          formData
        ),
    };
  }
}

export const getAxiosErrorDetails = (err: unknown) => {
  if (err instanceof AxiosError) {
    return {
      detail: err.response?.data?.detail,
      status: err.response?.status,
    };
  }
  return { detail: "Unknown error", status: 500 };
};

// Export singleton instance
export const httpClient = HttpClient.getInstance();
