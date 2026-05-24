import { type ReactNode, useEffect, useState } from "react";
import {
  type HttpErrorDetails,
  subscribeToHttpErrors,
} from "@/lib/httpClient";
import { BILLING_ERROR_CODES } from "../payments.constants";
import type { BillingEntitlementRequiredError } from "../payments.types";
import { getCurrentReturnPath } from "../routing/payments-redirect";
import UpgradePlansModal from "../ui/UpgradePlansModal";

const isBillingEntitlementRequiredError = (
  data: unknown
): data is BillingEntitlementRequiredError => {
  if (!data || typeof data !== "object") {
    return false;
  }

  return (
    "code" in data &&
    data.code === BILLING_ERROR_CODES.ENTITLEMENT_REQUIRED &&
    "requiredFeature" in data &&
    typeof data.requiredFeature === "string"
  );
};

type UpgradeFlowState = {
  isOpen: boolean;
  requiredFeature: string | null;
  returnPath: string | null;
};

export function PaymentsUpgradeFlowProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [state, setState] = useState<UpgradeFlowState>({
    isOpen: false,
    requiredFeature: null,
    returnPath: null,
  });

  useEffect(() => {
    return subscribeToHttpErrors((details: HttpErrorDetails) => {
      if (!isBillingEntitlementRequiredError(details.data)) {
        return;
      }

      setState({
        isOpen: true,
        requiredFeature: details.data.requiredFeature,
        returnPath: getCurrentReturnPath(),
      });
    });
  }, []);

  const handleDismiss = () => {
    setState({
      isOpen: false,
      requiredFeature: null,
      returnPath: null,
    });
  };

  return (
    <>
      {children}
      <UpgradePlansModal
        open={state.isOpen}
        onDismiss={handleDismiss}
        requiredFeature={state.requiredFeature}
        returnPath={state.returnPath}
      />
    </>
  );
}
