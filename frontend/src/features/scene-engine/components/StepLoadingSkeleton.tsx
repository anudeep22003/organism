import { Skeleton } from "./Skeleton";

export function StepLoadingSkeleton() {
  return (
    <div className="flex h-full w-full flex-col gap-2 p-4">
      <Skeleton className="min-h-0 flex-1 w-full" />
      <Skeleton className="min-h-0 flex-1 w-full" />
      <Skeleton className="min-h-0 flex-1 w-full" />
    </div>
  );
}
