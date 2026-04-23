import { queryOptions } from "@tanstack/react-query";
import { authApi } from "./auth.api";
import { authKeys } from "./auth.query-keys";

export const meQueryOptions = () =>
  queryOptions({
    queryKey: authKeys.me(),
    queryFn: authApi.fetchCurrentUser,
    staleTime: 60_000,
    retry: false,
  });
