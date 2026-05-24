export type CreateCheckoutSessionRequest = {
  planId: string;
  returnPath?: string | null;
};

export type CreateCheckoutSessionResponse = {
  checkoutUrl: string;
};
