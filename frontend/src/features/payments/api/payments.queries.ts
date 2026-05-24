import { queryOptions } from "@tanstack/react-query";
import { PAYMENTS_QUERY_ROOT } from "../payments.constants";
import { paymentsApi } from "./payments.api";

export const billingMeOptions = () =>
  queryOptions({
    queryKey: [...PAYMENTS_QUERY_ROOT, "billing-me"] as const,
    queryFn: paymentsApi.fetchBillingMe,
    staleTime: 60_000,
  });
