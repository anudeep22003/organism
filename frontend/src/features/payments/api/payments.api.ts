import { httpClient } from "@/lib/httpClient";
import { BILLING_SERVICE_ENDPOINTS } from "./payments.constants";

type CheckoutSessionResponse = {
  url: string;
};

export const paymentsApi = {
  createCheckoutSession: async () => {
    return await httpClient.post<CheckoutSessionResponse>(
      BILLING_SERVICE_ENDPOINTS.CREATE_CHECKOUT_SESSION,
      {}
    );
  },

  startCheckout: async () => {
    const { url } = await paymentsApi.createCheckoutSession();
    window.location.assign(url);
  },
};
