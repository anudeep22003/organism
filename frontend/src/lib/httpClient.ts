import { BACKEND_URL } from "@/constants";
import { AUTH_SERVICE_ENDPOINTS } from "@/features/auth/api/auth.constants";
import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import { apiLogger, authLogger } from "./logger";

const HTTP_STATUS_UNAUTHORIZED = 401;
const CSRF_COOKIE_NAME = "csrf_token";
const CSRF_HEADER_NAME = "X-CSRF-Token";
const UNSAFE_HTTP_METHODS = new Set([
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
]);

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

/*
HttpClient is the auth transport boundary.

High-level flow:

1. every request is sent with `withCredentials: true`, so auth cookies travel
   automatically with same-site requests
2. unsafe requests mirror the `csrf_token` cookie into `X-CSRF-Token`
3. if a request comes back `401`, the client tries one shared
   `POST /api/auth/refresh`
4. after a successful refresh, the original request is retried once

What this class intentionally does not do:

- it does not own React auth state
- it does not decide routing
- it does not expose a frontend-readable access token

That separation keeps auth policy in `src/features/auth` and transport
mechanics here.
*/
class HttpClient {
  private static instance: HttpClient;
  private axiosInstance: AxiosInstance;
  private refreshPromise: Promise<void> | null = null;

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

  public async refreshSession(): Promise<void> {
    /*
    Refresh is deduplicated behind one shared promise. If several requests hit
    `401` together, they all await the same refresh instead of stampeding the
    backend with parallel refresh calls.
    */
    if (this.refreshPromise) {
      authLogger.debug("Awaiting ongoing auth refresh");
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      await this.axiosInstance.post<void>(
        AUTH_SERVICE_ENDPOINTS.REFRESH,
        {}
      );
    })();

    try {
      await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private shouldAttemptRefresh(error: AxiosError): boolean {
    const request = error.config as RetryableRequestConfig | undefined;
    const isUnauthorized =
      error.response?.status === HTTP_STATUS_UNAUTHORIZED;
    const isRefreshRequest = request?.url?.includes(
      this.getRefreshEndpoint()
    );
    const isLogoutRequest = request?.url?.includes(
      this.getLogoutEndpoint()
    );

    return (
      isUnauthorized &&
      request?._retry !== true &&
      !isRefreshRequest &&
      !isLogoutRequest
    );
  }

  public async *streamPost<T = unknown>(
    url: string,
    data?: unknown
  ): AsyncGenerator<T> {
    /*
    Streaming uses `fetch` instead of Axios, but it follows the same auth
    contract: send cookies, send CSRF for unsafe requests, refresh once on
    `401`, then retry the stream.
    */
    const response = await fetch(`${BACKEND_URL}${url}`, {
      method: "POST",
      headers: this.buildFetchHeaders(),
      body: JSON.stringify(data),
      credentials: "include",
    });

    if (response.status === HTTP_STATUS_UNAUTHORIZED) {
      await this.refreshSession();
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

  private getRefreshEndpoint() {
    return AUTH_SERVICE_ENDPOINTS.REFRESH;
  }

  private getLogoutEndpoint() {
    return AUTH_SERVICE_ENDPOINTS.LOGOUT;
  }

  private readCookie(name: string) {
    if (typeof document === "undefined") {
      return null;
    }

    const encodedName = encodeURIComponent(name);
    const cookies = document.cookie.split("; ");

    for (const cookie of cookies) {
      const [rawName, ...rawValueParts] = cookie.split("=");
      if (rawName !== encodedName) {
        continue;
      }

      return decodeURIComponent(rawValueParts.join("="));
    }

    return null;
  }

  private getCsrfToken() {
    return this.readCookie(CSRF_COOKIE_NAME);
  }

  private isUnsafeMethod(method: string | undefined) {
    if (!method) {
      return false;
    }

    return UNSAFE_HTTP_METHODS.has(method.toUpperCase());
  }

  private setHeader(
    config: InternalAxiosRequestConfig,
    key: string,
    value: string | undefined
  ) {
    const nextHeaders = AxiosHeaders.from(config.headers);
    if (value === undefined) {
      nextHeaders.delete(key);
    } else {
      nextHeaders.set(key, value);
    }

    config.headers = nextHeaders;
  }

  private buildFetchHeaders() {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const csrfToken = this.getCsrfToken();
    if (csrfToken) {
      headers[CSRF_HEADER_NAME] = csrfToken;
    }

    return headers;
  }

  private setupInterceptors(): void {
    /*
    Request interceptor:
    - attach CSRF on unsafe methods

    Response interceptor:
    - on `401`, try one refresh and replay the original request once
    */
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const csrfToken = this.getCsrfToken();
        if (csrfToken && this.isUnsafeMethod(config.method)) {
          this.setHeader(config, CSRF_HEADER_NAME, csrfToken);
        }

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
        const originalRequest = error.config as
          | RetryableRequestConfig
          | undefined;

        if (originalRequest && this.shouldAttemptRefresh(error)) {
          try {
            originalRequest._retry = true;
            await this.refreshSession();
            return this.axiosInstance.request(originalRequest);
          } catch (refreshError) {
            authLogger.debug("Refresh failed", refreshError);
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
