import { useEffect, useRef, useState } from "react";

const CIRCLE_RADIUS = 6;
const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS;

type ValidationErrorBlockProps = {
  message: string;
  durationMs?: number;
  onClear?: () => void;
  dismissible?: boolean;
};

export function ValidationErrorBlock({
  message,
  durationMs = 5000,
  onClear,
  dismissible = true,
}: ValidationErrorBlockProps) {
  const [progress, setProgress] = useState(1);
  const startTime = useRef<number>(Date.now());
  const rafRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    startTime.current = Date.now();
    setProgress(1);

    if (durationMs === Infinity) return;

    const tick = () => {
      const elapsed = Date.now() - startTime.current;
      const remaining = Math.max(0, 1 - elapsed / durationMs);
      setProgress(remaining);
      if (remaining > 0) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);

    timerRef.current = setTimeout(() => {
      onClear?.();
    }, durationMs);

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      if (timerRef.current !== null) clearTimeout(timerRef.current);
    };
  }, [durationMs, onClear]);

  const handleDismiss = () => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    if (timerRef.current !== null) clearTimeout(timerRef.current);
    onClear?.();
  };

  const dashOffset = CIRCLE_CIRCUMFERENCE * (1 - progress);

  return (
    <div className="shrink-0 flex items-center gap-2 border-b border-border bg-destructive/5 px-3 py-1.5">
      {durationMs !== Infinity && (
        <svg width="16" height="16" className="-rotate-90 shrink-0">
          <circle
            cx="8"
            cy="8"
            r={CIRCLE_RADIUS}
            fill="none"
            strokeWidth="1.5"
            className="stroke-destructive/20"
          />
          <circle
            cx="8"
            cy="8"
            r={CIRCLE_RADIUS}
            fill="none"
            strokeWidth="1.5"
            strokeLinecap="square"
            strokeDasharray={CIRCLE_CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
            className="stroke-destructive/60"
          />
        </svg>
      )}
      <span className="flex-1 text-[10px] text-destructive">{message}</span>
      {dismissible && (
        <button
          onClick={handleDismiss}
          className="text-[10px] text-destructive/60 hover:text-destructive"
        >
          ✕
        </button>
      )}
    </div>
  );
}
