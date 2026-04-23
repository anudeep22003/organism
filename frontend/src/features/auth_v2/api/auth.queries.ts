import { queryOptions } from "@tanstack/react-query";
import { authV2Api } from "./auth.api";
import { authV2Keys } from "./auth.query-keys";

export const meQueryOptions = () =>
  queryOptions({
    queryKey: authV2Keys.me(),
    queryFn: authV2Api.fetchCurrentUser,
    staleTime: 60_000,
    retry: false,
  });
