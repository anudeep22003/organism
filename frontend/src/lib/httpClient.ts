import { BACKEND_URL } from "@/constants";
import axios, { type AxiosInstance } from "axios";
import { apiLogger } from "./logger";

class HttpClient {
  private static instance: HttpClient;
  private axiosInstance: AxiosInstance;

  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: BACKEND_URL,
      withCredentials: true,
      timeout: 30000, // 30 seconds timeout
    });

    this.setupInterceptors();
  }

  public async post<T = unknown>(url: string, data?: unknown): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data);
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

  private setupInterceptors(): void {
    // Request interceptor
    this.axiosInstance.interceptors.request.use(
      (config) => {
        apiLogger.debug("HTTP Request", {
          method: config.method?.toUpperCase(),
          url: config.url,
          baseURL: config.baseURL,
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
      (error) => {
        apiLogger.error("HTTP Response Error", {
          status: error.response?.status,
          message: error.message,
          url: error.config?.url,
        });
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

// Export singleton instance
export const httpClient = HttpClient.getInstance();
