import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { useSceneEngine } from "@scene-engine/context";
import { imageSignedUrlOptions } from "@scene-engine/core/scene-engine.queries";
import type { CharacterBundle } from "../../character.types";
import type { ImageRecord } from "@scene-engine/core/scene-engine.types";
import { useCharacterRendering } from "../hooks/useCharacterRendering";

type CharacterRenderBlockProps = {
  bundle: CharacterBundle;
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

function CharacterRenderBlock({ bundle, onActivate, onRender, isRendering, errorMessage }: CharacterRenderBlockProps) {
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
                {bundle.character.name}
              </span>
            )}
            {hasRender && (
              <span className="absolute bottom-3 left-3 bg-background px-2 py-1 text-xs text-foreground">
                {bundle.character.name}
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

type CharacterRenderingListProps = {
  characters: CharacterBundle[];
  onActivate: (characterId: string) => void;
};

export function CharacterRenderingList({ characters, onActivate }: CharacterRenderingListProps) {
  const { projectId, storyId } = useSceneEngine();
  const { triggerRender, renderingIds, errorIds } = useCharacterRendering(projectId, storyId);

  return (
    <div className="flex h-full w-full flex-col items-center gap-2 overflow-y-auto p-4">
      {characters.map((bundle) => (
        <CharacterRenderBlock
          key={bundle.character.id}
          bundle={bundle}
          onActivate={() => onActivate(bundle.character.id)}
          onRender={() => triggerRender({ characterId: bundle.character.id })}
          isRendering={renderingIds.has(bundle.character.id)}
          errorMessage={errorIds.get(bundle.character.id) ?? null}
        />
      ))}
    </div>
  );
}
