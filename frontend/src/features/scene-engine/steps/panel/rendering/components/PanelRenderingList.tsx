import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { useSceneEngine } from "@scene-engine/context";
import { imageSignedUrlOptions } from "@scene-engine/shared/scene-engine.queries";
import type { PanelBundle } from "../../panel.types";
import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";
import { usePanelRendering } from "../hooks/usePanelRendering";

type PanelRenderBlockProps = {
  bundle: PanelBundle;
  displayIndex: number;
  onActivate: () => void;
  onRender: () => void;
  isRendering: boolean;
  errorMessage: string | null;
};

function RenderedImage({ render }: { render: ImageRecord }) {
  const queryClient = useQueryClient();
  const { data } = useQuery(imageSignedUrlOptions(render.id));

  return (
    <div className="absolute inset-0">
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

function PanelRenderBlock({ bundle, displayIndex, onActivate, onRender, isRendering, errorMessage }: PanelRenderBlockProps) {
  const hasRender = bundle.canonicalRender !== null;

  return (
    <div
      className={bundle.canonicalRender ? "aspect-square w-full max-w-lg shrink-0" : "h-48 w-full max-w-lg shrink-0"}
      onClick={onActivate}
    >
      <div className="relative flex h-full w-full cursor-pointer items-center justify-center border border-border bg-muted/20 hover:bg-muted/40">
        {isRendering ? (
          <>
            <Skeleton className="absolute inset-0" />
            <span className="relative text-xs text-muted-foreground">Rendering…</span>
          </>
        ) : (
          <>
            {hasRender && <RenderedImage render={bundle.canonicalRender!} />}
            {!hasRender && (
              <span className="text-xs text-muted-foreground">
                Panel {displayIndex}
              </span>
            )}
            {hasRender && (
              <span className="absolute bottom-3 left-3 bg-background px-2 py-1 text-xs text-foreground">
                Panel {displayIndex}
              </span>
            )}
            <div className="absolute bottom-3 right-3 flex items-center gap-2">
              {errorMessage && (
                <span className="bg-background px-2 py-1 text-[10px] text-destructive">
                  {errorMessage}
                </span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (hasRender) { onActivate(); } else { onRender(); }
                }}
                className="bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80"
              >
                {hasRender ? "Edit" : "Render"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

type PanelRenderingListProps = {
  panels: PanelBundle[];
  onActivate: (panelId: string) => void;
};

export function PanelRenderingList({ panels, onActivate }: PanelRenderingListProps) {
  const { projectId, storyId } = useSceneEngine();
  const { triggerRender, renderingIds, errorIds } = usePanelRendering(projectId, storyId);

  return (
    <div className="flex h-full w-full flex-col items-center gap-2 overflow-y-auto p-4">
      {panels.map((bundle, index) => (
        <PanelRenderBlock
          key={bundle.panel.id}
          bundle={bundle}
          displayIndex={index + 1}
          onActivate={() => onActivate(bundle.panel.id)}
          onRender={() => triggerRender({ panelId: bundle.panel.id })}
          isRendering={renderingIds.has(bundle.panel.id)}
          errorMessage={errorIds.get(bundle.panel.id) ?? null}
        />
      ))}
    </div>
  );
}
