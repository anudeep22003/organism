import type { ReactNode } from "react";

interface AuthOutcomePageProps {
  children?: ReactNode;
  description: string;
  footer?: ReactNode;
  title: string;
}

const AuthOutcomePage = ({
  children,
  description,
  footer,
  title,
}: AuthOutcomePageProps) => {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.16),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,188,5,0.18),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(52,168,83,0.14),transparent_28%),linear-gradient(180deg,rgba(250,250,250,0.95),rgba(244,244,245,0.92))] dark:bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.18),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,188,5,0.14),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(52,168,83,0.12),transparent_28%),linear-gradient(180deg,rgba(10,10,10,0.98),rgba(24,24,27,0.96))]" />
      </div>

      <div className="relative flex shrink-0 items-center border-b border-border bg-background/70 px-4 py-1.5 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Organism</span>
          <div className="h-2.5 w-px bg-border" />
          <span className="text-[10px] text-foreground">Auth callback</span>
        </div>
      </div>

      <div className="relative flex min-h-0 flex-1 items-center justify-center p-4">
        <div className="flex w-full max-w-2xl flex-col border border-border bg-background/72 shadow-[0_24px_80px_rgba(0,0,0,0.06)] backdrop-blur-md dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
          <div className="flex flex-col gap-6 px-4 py-8 sm:px-6">
            <div className="space-y-2">
              <h1 className="text-base text-foreground">{title}</h1>
              <p className="text-xs text-muted-foreground">{description}</p>
            </div>

            {children}
            {footer}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthOutcomePage;
