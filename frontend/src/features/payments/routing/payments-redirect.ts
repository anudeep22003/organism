const POST_CHECKOUT_RETURN_PATH_STORAGE_KEY = "payments.return-path";
const RETURN_PATH_QUERY_PARAM = "returnPath";

const isSafeInternalRedirect = (
  redirectTarget: string | null | undefined
) => {
  return Boolean(
    redirectTarget &&
      redirectTarget.startsWith("/") &&
      !redirectTarget.startsWith("//")
  );
};

export const getSafeReturnPath = (
  returnPath: string | null | undefined
) => {
  if (!isSafeInternalRedirect(returnPath)) {
    return null;
  }

  return returnPath;
};

export const getReturnPathFromSearchParams = (search: string) => {
  const params = new URLSearchParams(search);
  return getSafeReturnPath(params.get(RETURN_PATH_QUERY_PARAM));
};

const canUseSessionStorage = () => {
  return typeof window !== "undefined";
};

export const persistCheckoutReturnPath = (
  returnPath: string | null | undefined
) => {
  const safeReturnPath = getSafeReturnPath(returnPath);

  if (!canUseSessionStorage()) {
    return;
  }

  if (!safeReturnPath) {
    window.sessionStorage.removeItem(
      POST_CHECKOUT_RETURN_PATH_STORAGE_KEY
    );
    return;
  }

  window.sessionStorage.setItem(
    POST_CHECKOUT_RETURN_PATH_STORAGE_KEY,
    safeReturnPath
  );
};

export const consumeCheckoutReturnPath = () => {
  if (!canUseSessionStorage()) {
    return null;
  }

  const returnPath = window.sessionStorage.getItem(
    POST_CHECKOUT_RETURN_PATH_STORAGE_KEY
  );
  window.sessionStorage.removeItem(
    POST_CHECKOUT_RETURN_PATH_STORAGE_KEY
  );
  return getSafeReturnPath(returnPath);
};

export const buildPaymentsRoute = ({
  returnPath,
}: {
  returnPath?: string | null;
}) => {
  const safeReturnPath = getSafeReturnPath(returnPath);
  if (!safeReturnPath) {
    return "/payments";
  }

  const params = new URLSearchParams({
    [RETURN_PATH_QUERY_PARAM]: safeReturnPath,
  });

  return `/payments?${params.toString()}`;
};
