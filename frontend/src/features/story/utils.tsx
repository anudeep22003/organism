const renderFunction = (
  key: string,
  value: string | number | boolean | null | undefined,
): React.ReactNode => {
  return (
    <div>
      {key}: {value}
    </div>
  );
};

export const recursivePrinter = (
  object: Record<string, unknown>,
  renderFn: typeof renderFunction = renderFunction,
): React.ReactNode[] => {
  return Object.entries(object).map(([key, value]) => {
    if (typeof value === "object" && value !== null) {
      return recursivePrinter(
        value as Record<string, unknown>,
        renderFn,
      );
    }
    return renderFn(
      key,
      value as string | number | boolean | null | undefined,
    );
  });
};
