import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
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

const getBillingEntitlementRequiredError = (
  details: HttpErrorDetails
) => {
  if (isBillingEntitlementRequiredError(details.data)) {
    return details.data;
  }

  if (isBillingEntitlementRequiredError(details.detail)) {
    return details.detail;
  }

  return null;
};

type UpgradeFlowState = {
  isOpen: boolean;
  requiredFeature: string | null;
  returnPath: string | null;
};

type OpenUpgradeFlowOptions = {
  requiredFeature?: string | null;
  returnPath?: string | null;
};

type PaymentsUpgradeFlowContextValue = {
  closeUpgradeFlow: () => void;
  openUpgradeFlow: (options?: OpenUpgradeFlowOptions) => void;
};

const PaymentsUpgradeFlowContext =
  createContext<PaymentsUpgradeFlowContextValue | null>(null);

export const usePaymentsUpgradeFlow = () => {
  const context = useContext(PaymentsUpgradeFlowContext);

  if (!context) {
    throw new Error(
      "usePaymentsUpgradeFlow must be used inside PaymentsUpgradeFlowProvider"
    );
  }

  return context;
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

  const closeUpgradeFlow = useCallback(() => {
    setState({
      isOpen: false,
      requiredFeature: null,
      returnPath: null,
    });
  }, []);

  const openUpgradeFlow = useCallback(
    (options: OpenUpgradeFlowOptions = {}) => {
      const returnPath = options.returnPath ?? getCurrentReturnPath();

      setState({
        isOpen: true,
        requiredFeature: options.requiredFeature ?? null,
        returnPath,
      });
    },
    []
  );

  useEffect(() => {
    const unsubscribeFromHttpErrors = subscribeToHttpErrors(
      (details: HttpErrorDetails) => {
        const entitlementError =
          getBillingEntitlementRequiredError(details);

        if (!entitlementError) {
          return;
        }

        const upgradeFlowOptions = {
          requiredFeature: entitlementError.requiredFeature,
        };

        openUpgradeFlow(upgradeFlowOptions);
      }
    );

    return unsubscribeFromHttpErrors;
  }, [openUpgradeFlow]);

  const contextValue = useMemo(() => {
    return {
      closeUpgradeFlow,
      openUpgradeFlow,
    };
  }, [closeUpgradeFlow, openUpgradeFlow]);

  return (
    <PaymentsUpgradeFlowContext.Provider value={contextValue}>
      {children}
      <UpgradePlansModal
        open={state.isOpen}
        onDismiss={closeUpgradeFlow}
        requiredFeature={state.requiredFeature}
        returnPath={state.returnPath}
      />
    </PaymentsUpgradeFlowContext.Provider>
  );
}
