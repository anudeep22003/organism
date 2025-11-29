import { BACKEND_URL } from "@/constants";
import axios, { AxiosError, type AxiosInstance } from "axios";
import { apiLogger, authLogger } from "./logger";
import {
  ACCESS_TOKEN_EXPIRY_TIME,
  AUTH_SERVICE_ENDPOINTS,
  HTTP_STATUS,
} from "@/pages/auth/constants";
import { type LoginResponse } from "@/pages/auth/types";

class HttpClient {
  private static instance: HttpClient;
  private axiosInstance: AxiosInstance;
  private accessToken: string | null = null;
  private updateReactStateCallback?: (token: string) => void;
  private refreshTimer: NodeJS.Timeout | null = null;

  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: BACKEND_URL,
      withCredentials: true,
      timeout: 30000, // 30 seconds timeout
    });

    this.setupInterceptors();
  }

  public setReactStateUpdateFn(callback: (token: string) => void) {
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

  public setAccessToken(token: string | null) {
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
    try {
      const { accessToken: newAccessToken } =
        await this.post<LoginResponse>(
          AUTH_SERVICE_ENDPOINTS.REFRESH,
          {}
          // this.accessToken ?? undefined
        );
      this.setAccessToken(newAccessToken);
    } catch (err) {
      throw new Error(`Error refreshing Access token, ${err}`);
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
        if (error.response?.status === HTTP_STATUS.UNAUTHORIZED)
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

// Export singleton instance
export const httpClient = HttpClient.getInstance();
