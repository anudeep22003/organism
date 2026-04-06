type ValidationErrorBlockProps = {
  message: string;
};

export function ValidationErrorBlock({ message }: ValidationErrorBlockProps) {
  return (
    <div className="shrink-0 border-b border-border bg-destructive/5 px-3 py-1.5">
      <span className="text-[10px] text-destructive">{message}</span>
    </div>
  );
}
