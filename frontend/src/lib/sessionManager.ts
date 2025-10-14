import { BACKEND_URL } from "@/constants";
import axios from "axios";

interface Session {
  sessionId: string;
  message: string;
}

interface ValidateSessionResponse {
  valid: boolean;
  message: string;
}

interface DestroySessionResponse {
  message: string;
}

const axiosClient = axios.create({
  baseURL: `${BACKEND_URL}/api/session`,
  withCredentials: true,
});

export class SessionManager {
  public static async createSession(): Promise<Session> {
    const response = await axiosClient.post<Session>("/create");
    return response.data;
  }

  public static async validateSession(): Promise<ValidateSessionResponse> {
    const response = await axiosClient.get<ValidateSessionResponse>(
      "/validate"
    );
    return response.data;
  }

  public static async destroySession() {
    const response = await axiosClient.post<DestroySessionResponse>(
      "/destroy"
    );
    return response.data;
  }
}
