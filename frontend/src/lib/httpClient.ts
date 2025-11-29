import { BACKEND_URL } from "@/constants";
import axios, { AxiosError, type AxiosInstance } from "axios";
import { apiLogger, authLogger } from "./logger";
import { HTTP_STATUS } from "@/pages/auth/constants";
import authService from "@/pages/auth/services/authService";

class HttpClient {
  private static instance: HttpClient;
  private axiosInstance: AxiosInstance;
  private accessToken: string | null = null;
  private updateReactState?: (token: string) => void;

  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: BACKEND_URL,
      withCredentials: true,
      timeout: 30000, // 30 seconds timeout
    });

    this.setupInterceptors();
  }

  public setReactStateUpdateFn(callback: (token: string) => void) {
    this.updateReactState = callback;
  }

  public async post<T = unknown>(
    url: string,
    data?: unknown,
    accessToken?: string
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data, {
        // headers: {
        //   Authorization: `Bearer ${accessToken}`,
        // },
      });
      return response.data;
    } catch (error) {
      apiLogger.error("HTTP Request Error", { error });
      throw error;
    }
  }

  public async get<T = unknown>(
    url: string,
    accessToken?: string
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(url, {
        // headers: {
        //   Authorization: `Bearer ${accessToken}`,
        // },
      });
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

  private setAccessToken(token: string | null) {
    if (!token) {
      throw new Error("Null access token being tried to set");
    }
    this.accessToken = token;
    if (this.updateReactState) {
      this.updateReactState(token);
    }
  }
  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // TODO set the Authorization globally
        config.headers.Authorization = `Bearer ${this.accessToken}`;
        apiLogger.debug("HTTP Request", {
          method: config.method?.toUpperCase(),
          url: config.url,
          baseURL: config.baseURL,
          headers: config.headers,
        });
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
        if (error.response?.status === HTTP_STATUS.UNAUTHORIZED)
          authLogger.debug(
            "No accessToken or unauthorized meaning token expired. Will attempt refresh",
            error,
            "current accessToken = ",
            this.accessToken
          );
        try {
          // TODO is passing an accessToken in there correct, or should it be empty?
          const { accessToken: newAccessToken } =
            await authService.refreshAccessToken(this.accessToken);
          this.setAccessToken(newAccessToken);

          // Retry the failed request
          error.config.headers.Authorization = `Bearer ${newAccessToken}`;
          authLogger.debug("Reattempting the failed request.");
          return this.axiosInstance.request(error.config);
        } catch (refreshError) {
          // add an onAuthFailure callback here to let react know of the failure
          authLogger.debug("Refresh failed", refreshError);
        }
        // apiLogger.error("HTTP Response Error", {
        //   status: error.response?.status,
        //   message: error.message,
        //   url: error.config?.url,
        // });
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
