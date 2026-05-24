import { httpClient } from "@/lib/httpClient";
import { TEST_CHECKOUT_PLAN_ID } from "../payments.constants";
import type {
  BillingMeResponse,
  CreateCheckoutSessionRequest,
  CreateCheckoutSessionResponse,
} from "../payments.types";
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

  startCheckout: async (
    payload: CreateCheckoutSessionRequest = {
      planId: TEST_CHECKOUT_PLAN_ID,
    }
  ) => {
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
};
