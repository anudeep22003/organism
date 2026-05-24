import { queryOptions } from "@tanstack/react-query";
import { PAYMENTS_QUERY_ROOT } from "../payments.constants";
import { paymentsApi } from "./payments.api";

const ONE_DAY_MS = 86_400_000;

export const billingMeOptions = () =>
  queryOptions({
    queryKey: [...PAYMENTS_QUERY_ROOT, "billing-me"] as const,
    queryFn: paymentsApi.fetchBillingMe,
    staleTime: 60_000,
  });

export const plansOptions = () =>
  queryOptions({
    queryKey: [...PAYMENTS_QUERY_ROOT, "plans"] as const,
    queryFn: paymentsApi.fetchPlans,
    staleTime: ONE_DAY_MS,
  });
