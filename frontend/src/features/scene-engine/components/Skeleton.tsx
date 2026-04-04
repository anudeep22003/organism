import type { CSSProperties } from "react";

type SkeletonProps = {
  className?: string;
  style?: CSSProperties;
};

export function Skeleton({ className = "", style }: SkeletonProps) {
  return (
    <div className={`animate-pulse bg-muted ${className}`} style={style} />
  );
}
