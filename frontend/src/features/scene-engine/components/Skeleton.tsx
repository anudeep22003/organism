import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

const CIRCLE_RADIUS = 32;
const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS;
const TIMER_CYCLE_SECONDS = 60;

function CircularTimer({ elapsed }: { elapsed: number }) {
  const position = elapsed % TIMER_CYCLE_SECONDS;
  const progress = position / TIMER_CYCLE_SECONDS;
  const dashOffset = CIRCLE_CIRCUMFERENCE * progress;

  return (
    <div className="relative flex items-center justify-center">
      <svg width="80" height="80" className="-rotate-90">
        <circle
          cx="40"
          cy="40"
          r={CIRCLE_RADIUS}
          fill="none"
          strokeWidth="2"
          className="stroke-foreground/20"
        />
        <circle
          cx="40"
          cy="40"
          r={CIRCLE_RADIUS}
          fill="none"
          strokeWidth="2"
          strokeLinecap="square"
          strokeDasharray={CIRCLE_CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          className="stroke-foreground/40 transition-all duration-1000"
        />
      </svg>
      <span className="absolute text-xl tabular-nums text-foreground/40">
        {elapsed}s
      </span>
    </div>
  );
}

type SkeletonProps = {
  className?: string;
  style?: CSSProperties;
  label?: string;
  showTimer?: boolean;
};

export function Skeleton({ className = "", style, label, showTimer }: SkeletonProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!showTimer) return;
    const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [showTimer]);

  const hasOverlay = label || showTimer;

  return (
    <div
      className={`relative animate-pulse bg-foreground/10 ${className}`}
      style={style}
    >
      {hasOverlay && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          {label && (
            <span className="text-xs text-foreground/40">{label}</span>
          )}
          {showTimer && <CircularTimer elapsed={elapsed} />}
        </div>
      )}
    </div>
  );
}
