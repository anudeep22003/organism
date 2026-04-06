import type { ReactNode } from "react";

type ModalShellProps = {
  header: ReactNode;
  onDismiss: () => void;
  children: ReactNode;
  zClass?: string;
  headerActions?: ReactNode;
};

export function ModalShell({
  header,
  onDismiss,
  children,
  zClass = "z-20",
  headerActions,
}: ModalShellProps) {
  return (
    <>
      <div className="absolute inset-0 z-10 backdrop-blur-sm pointer-events-none" />

      <div
        className={`absolute inset-0 ${zClass} flex items-center justify-center p-4`}
        onClick={onDismiss}
      >
        <div
          className="flex w-full max-w-2xl h-full flex-col border border-border bg-background"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex shrink-0 items-center justify-between border-b border-border px-3 py-2">
            <div className="min-w-0 flex-1">
              {typeof header === "string" ? (
                <span className="text-xs text-muted-foreground">{header}</span>
              ) : (
                header
              )}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {headerActions}
              <button
                onClick={onDismiss}
                className="bg-foreground px-2 py-1 text-[10px] text-background hover:bg-foreground/80"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">{children}</div>
        </div>
      </div>
    </>
  );
}
