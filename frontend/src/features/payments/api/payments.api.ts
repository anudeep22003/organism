import { httpClient } from "@/lib/httpClient";
import type {
  BillingMeResponse,
  CreateCheckoutSessionRequest,
  CreateCheckoutSessionResponse,
  ListPlansResponse,
} from "../payments.types";
import { persistCheckoutReturnPath } from "../routing/payments-redirect";
import { BILLING_SERVICE_ENDPOINTS } from "./payments.constants";

export const paymentsApi = {
  createCheckoutSession: async (
    payload: CreateCheckoutSessionRequest
  ) => {
    return await httpClient.post<CreateCheckoutSessionResponse>(
      BILLING_SERVICE_ENDPOINTS.CREATE_CHECKOUT_SESSION,
      payload
    );
  },

  startCheckout: async (payload: CreateCheckoutSessionRequest) => {
    persistCheckoutReturnPath(payload.returnPath);
    const { checkoutUrl } = await paymentsApi.createCheckoutSession(
      payload
    );
    window.location.assign(checkoutUrl);
  },

  fetchBillingMe: async () => {
    return await httpClient.get<BillingMeResponse>(
      BILLING_SERVICE_ENDPOINTS.BILLING_ME
    );
  },

  fetchPlans: async () => {
    return await httpClient.get<ListPlansResponse>(
      BILLING_SERVICE_ENDPOINTS.PLANS
    );
  },
};
