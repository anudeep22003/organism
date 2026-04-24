import { QueryClient } from "@tanstack/react-query";
import { getAxiosErrorDetails } from "@/lib/httpClient";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        const { status } = getAxiosErrorDetails(error);
        if (status === 401) {
          return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});
