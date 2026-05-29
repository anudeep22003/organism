import { httpClient } from "@/lib/httpClient";
import { getAxiosErrorDetails } from "@/lib/httpClient";
import { buildAuthRoute } from "@/features/auth/routing/auth-redirect";
import type {
  BillingMeResponse,
  BillingPortalResponse,
  CreateCheckoutSessionRequest,
  CreateCheckoutSessionResponse,
  ListPlansResponse,
} from "../payments.types";
import {
  getCurrentReturnPath,
  getSafeReturnPath,
  persistCheckoutReturnPath,
} from "../routing/payments-redirect";
import { BILLING_SERVICE_ENDPOINTS } from "./payments.constants";

const CHECKOUT_AUTH_REQUIRED_ERROR_CODE = "auth_required";

const isCheckoutAuthRequiredError = (data: unknown) => {
  if (!data || typeof data !== "object") {
    return false;
  }

  return (
    "code" in data && data.code === CHECKOUT_AUTH_REQUIRED_ERROR_CODE
  );
};

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
    try {
      const { checkoutUrl } = await paymentsApi.createCheckoutSession(
        payload
      );
      persistCheckoutReturnPath(payload.returnPath);
      window.location.assign(checkoutUrl);
    } catch (error) {
      const details = getAxiosErrorDetails(error);

      if (
        isCheckoutAuthRequiredError(details.data) ||
        isCheckoutAuthRequiredError(details.detail)
      ) {
        const safePayloadReturnPath = getSafeReturnPath(
          payload.returnPath
        );
        const redirectTo =
          safePayloadReturnPath ?? getCurrentReturnPath() ?? "/";

        window.location.assign(buildAuthRoute({ redirectTo }));
        return;
      }

      throw error;
    }
  },

  fetchBillingMe: async () => {
    return await httpClient.get<BillingMeResponse>(
      BILLING_SERVICE_ENDPOINTS.BILLING_ME
    );
  },

  fetchCustomerPortal: async () => {
    return await httpClient.get<BillingPortalResponse>(
      BILLING_SERVICE_ENDPOINTS.CUSTOMER_PORTAL
    );
  },

  fetchPlans: async () => {
    return await httpClient.get<ListPlansResponse>(
      BILLING_SERVICE_ENDPOINTS.PLANS
    );
  },
};
