const AuthLoadingScreen = ({
  description = "Please wait a moment...",
  title = "Authenticating",
}: {
  description?: string;
  title?: string;
}) => {
  return (
    <div
      className="relative flex min-h-screen flex-col overflow-hidden bg-background"
      role="status"
      aria-live="polite"
      aria-label={title}
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.16),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,188,5,0.18),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(52,168,83,0.14),transparent_28%),linear-gradient(180deg,rgba(250,250,250,0.95),rgba(244,244,245,0.92))] dark:bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.18),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(251,188,5,0.14),transparent_30%),radial-gradient(circle_at_50%_85%,rgba(52,168,83,0.12),transparent_28%),linear-gradient(180deg,rgba(10,10,10,0.98),rgba(24,24,27,0.96))]" />
      </div>

      <div className="relative flex min-h-0 flex-1 items-center justify-center p-4">
        <div className="flex w-full max-w-md flex-col items-center gap-6 border border-border bg-background/72 px-6 py-10 text-center shadow-[0_24px_80px_rgba(0,0,0,0.06)] backdrop-blur-md dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
          <div className="relative">
            <div className="h-14 w-14 animate-spin rounded-full border-4 border-zinc-200 border-t-zinc-900 dark:border-zinc-800 dark:border-t-zinc-100" />
            <div className="absolute inset-1 rounded-full border border-zinc-300/60 dark:border-zinc-700/70" />
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">{title}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLoadingScreen;
