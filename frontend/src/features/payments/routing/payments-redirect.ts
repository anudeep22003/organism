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
): string | null => {
  if (!isSafeInternalRedirect(returnPath)) {
    return null;
  }

  return returnPath ?? null;
};

export const getReturnPathFromSearchParams = (
  search: string
): string | null => {
  const params = new URLSearchParams(search);
  return getSafeReturnPath(params.get(RETURN_PATH_QUERY_PARAM));
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
