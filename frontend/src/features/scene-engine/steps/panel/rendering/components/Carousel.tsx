import { useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { imageSignedUrlOptions } from "@scene-engine/core/scene-engine.queries";
import type { ImageRecord } from "@scene-engine/core/scene-engine.types";

function CarouselImage({ render }: { render: ImageRecord }) {
  const queryClient = useQueryClient();
  const { data } = useQuery(imageSignedUrlOptions(render.id));

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      {data?.url ? (
        <img
          src={data.url}
          alt=""
          className="h-full w-full object-contain"
          onError={() =>
            void queryClient.invalidateQueries({
              queryKey: imageSignedUrlOptions(render.id).queryKey,
            })
          }
        />
      ) : (
        <Skeleton className="h-full w-full" />
      )}
    </div>
  );
}

type CarouselProps = {
  items: ImageRecord[];
  index: number;
  onIndexChange: (i: number) => void;
};

export function Carousel({ items, index, onIndexChange }: CarouselProps) {
  const touchStartX = useRef<number | null>(null);

  const setAndNotify = (i: number) => {
    onIndexChange(i);
  };

  const prev = () => setAndNotify(Math.max(0, index - 1));
  const next = () => setAndNotify(Math.min(items.length - 1, index + 1));

  const hasPrev = index > 0;
  const hasNext = index < items.length - 1;

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (diff > 40) next();
    else if (diff < -40) prev();
    touchStartX.current = null;
  };

  const current = items[index];

  return (
    <div
      className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden bg-muted/20"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {current && <CarouselImage render={current} />}

      {hasPrev && (
        <button
          onClick={prev}
          className="absolute left-2 top-1/2 -translate-y-1/2 bg-background px-2 py-1 text-xl text-foreground opacity-50 hover:opacity-100"
        >
          ‹
        </button>
      )}

      {hasNext && (
        <button
          onClick={next}
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-background px-2 py-1 text-xl text-foreground opacity-50 hover:opacity-100"
        >
          ›
        </button>
      )}

      {items.length > 1 && (
        <div className="absolute bottom-3 flex gap-1.5">
          {items.map((_, i) => (
            <div
              key={i}
              onClick={() => setAndNotify(i)}
              className={`h-1.5 w-1.5 cursor-pointer transition-colors ${
                i === index ? "bg-foreground" : "bg-border"
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
