import type { LoginResponse } from "..";
import { httpClient } from "@/lib/httpClient";
import { AxiosError } from "axios";

const useAuthEntry = () => {
  const getUser = async (accessToken: string) => {
    try {
      const response = await httpClient.get<LoginResponse>(
        "api/auth/me",
        accessToken
      );
      console.log("response", response);
    } catch (err) {
      console.log("error", err);
      if (err instanceof AxiosError) {
        console.log("Axios error:", err);
        const statusCode = err.response?.status ?? 500;
        console.log("statusCode", statusCode);
      }
    }
  };

  return { getUser };
};

export default useAuthEntry;
