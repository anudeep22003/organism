import { useEffect, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { imageSignedUrlOptions } from "@scene-engine/shared/scene-engine.queries";
import type { PanelBundle } from "../../panel/panel.types";
import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";

function PanelImage({ render }: { render: ImageRecord }) {
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

function NoRenderSlot({ displayIndex }: { displayIndex: number }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-muted/10">
      <span className="text-xs text-muted-foreground">Panel {displayIndex}</span>
      <span className="text-[10px] text-muted-foreground/60">
        No render yet — go back to Step 5 to render this panel.
      </span>
    </div>
  );
}

type ComicCarouselProps = {
  panels: PanelBundle[];
  index: number;
  onIndexChange: (i: number) => void;
};

export function ComicCarousel({ panels, index, onIndexChange }: ComicCarouselProps) {
  const touchStartX = useRef<number | null>(null);

  const prev = () => onIndexChange(Math.max(0, index - 1));
  const next = () => onIndexChange(Math.min(panels.length - 1, index + 1));

  const hasPrev = index > 0;
  const hasNext = index < panels.length - 1;

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") prev();
      else if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

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

  const current = panels[index];

  return (
    <div
      className="relative flex h-full w-full items-center justify-center overflow-hidden bg-background"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {current && (
        current.canonicalRender
          ? <PanelImage render={current.canonicalRender} />
          : <NoRenderSlot displayIndex={index + 1} />
      )}

      <span className="absolute left-3 top-3 bg-background/80 px-2 py-1 text-[10px] text-muted-foreground">
        Panel {index + 1} / {panels.length}
      </span>

      {hasPrev && (
        <button
          onClick={prev}
          className="absolute left-2 top-1/2 -translate-y-1/2 bg-background/80 px-2 py-1 text-xl text-foreground opacity-50 hover:opacity-100"
        >
          ‹
        </button>
      )}

      {hasNext && (
        <button
          onClick={next}
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-background/80 px-2 py-1 text-xl text-foreground opacity-50 hover:opacity-100"
        >
          ›
        </button>
      )}

      {panels.length > 1 && (
        <div className="absolute bottom-3 flex gap-1.5">
          {panels.map((_, i) => (
            <div
              key={i}
              onClick={() => onIndexChange(i)}
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
