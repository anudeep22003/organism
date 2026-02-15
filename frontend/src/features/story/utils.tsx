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
    if (Array.isArray(value)) {
      if (value.length === 0) return renderFn(key, "[]");
      return recursivePrinter(
        value as unknown as Record<string, unknown>,
        renderFn,
      );
    }
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
