import { BACKEND_URL } from "@/constants";
import { AUTH_SERVICE_ENDPOINTS } from "@/features/auth/api/auth.constants";
import axios, { AxiosError, type AxiosInstance } from "axios";
import { apiLogger, authLogger } from "./logger";

const ACCESS_TOKEN_EXPIRY_TIME = 1000 * 60 * 30;
const HTTP_STATUS_UNAUTHORIZED = 401;

type RefreshResponse = {
  accessToken: string;
};

class HttpClient {
  private static instance: HttpClient;
  private axiosInstance: AxiosInstance;
  private accessToken: string | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;
  private refreshPromise: Promise<void> | null = null;
  private accessTokenSubscribers = new Set<
    (token: string | null) => void
  >();

  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: BACKEND_URL,
      withCredentials: true,
      timeout: 30_000,
    });

    this.setupInterceptors();
  }

  public static getInstance(): HttpClient {
    if (!HttpClient.instance) {
      HttpClient.instance = new HttpClient();
    }
    return HttpClient.instance;
  }

  public subscribeToAccessToken(
    callback: (token: string | null) => void
  ) {
    this.accessTokenSubscribers.add(callback);
    callback(this.accessToken);

    return () => {
      this.accessTokenSubscribers.delete(callback);
    };
  }

  private notifyAccessTokenSubscribers() {
    for (const callback of this.accessTokenSubscribers) {
      callback(this.accessToken);
    }
  }

  public getAccessToken() {
    return this.accessToken;
  }

  public setAccessToken(token: string) {
    if (!token) {
      throw new Error("Null access token being tried to set");
    }

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    this.accessToken = token;

    this.refreshTimer = setTimeout(() => {
      void this.refreshAccessToken();
    }, ACCESS_TOKEN_EXPIRY_TIME);

    this.notifyAccessTokenSubscribers();
  }

  public async clearSession(): Promise<void> {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    this.refreshTimer = null;
    this.accessToken = null;

    this.notifyAccessTokenSubscribers();
    authLogger.debug("Cleared session");
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

  public async patch<T = unknown>(
    url: string,
    data?: unknown
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.patch<T>(url, data, {});
      return response.data;
    } catch (error) {
      apiLogger.error("HTTP Request Error", { error });
      throw error;
    }
  }

  public async delete<T = void>(url: string): Promise<T> {
    try {
      const response = await this.axiosInstance.delete<T>(url, {});
      return response.data;
    } catch (error) {
      apiLogger.error("HTTP Request Error", { error });
      throw error;
    }
  }

  public async refreshAccessToken(): Promise<void> {
    if (this.refreshPromise) {
      authLogger.debug("Awaiting ongoing access token refresh");
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      const { accessToken: newAccessToken } =
        await this.post<RefreshResponse>(
          AUTH_SERVICE_ENDPOINTS.REFRESH,
          {}
        );
      this.setAccessToken(newAccessToken);
    })();

    try {
      await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private shouldAttemptRefresh(error: AxiosError): boolean {
    const isUnauthorized =
      error.response?.status === HTTP_STATUS_UNAUTHORIZED;
    const isRefreshRequest = error.config?.url?.includes(
      AUTH_SERVICE_ENDPOINTS.REFRESH
    );
    const isLogoutRequest = error.config?.url?.includes(
      AUTH_SERVICE_ENDPOINTS.LOGOUT
    );

    return isUnauthorized && !isRefreshRequest && !isLogoutRequest;
  }

  public async *streamPost<T = unknown>(
    url: string,
    data?: unknown
  ): AsyncGenerator<T> {
    const response = await fetch(`${BACKEND_URL}${url}`, {
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

    if (response.status === HTTP_STATUS_UNAUTHORIZED) {
      await this.refreshAccessToken();
      yield* this.streamPost(url, data);
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
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        yield JSON.parse(line) as T;
      }
    }

    if (buffer.trim()) {
      yield JSON.parse(buffer) as T;
    }
  }

  private setupInterceptors(): void {
    this.axiosInstance.interceptors.request.use(
      (config) => {
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

    this.axiosInstance.interceptors.response.use(
      (response) => {
        apiLogger.debug("HTTP Response", {
          status: response.status,
          url: response.config.url,
        });
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        if (this.shouldAttemptRefresh(error)) {
          try {
            await this.refreshAccessToken();
            return this.axiosInstance.request(originalRequest);
          } catch (refreshError) {
            authLogger.debug("Refresh failed", refreshError);
            await this.clearSession();
          }
        }

        return Promise.reject(error);
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

export const httpClient = HttpClient.getInstance();
