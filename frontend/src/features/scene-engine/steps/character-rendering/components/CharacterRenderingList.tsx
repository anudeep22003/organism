import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "../../../components/Skeleton";
import { useSceneEngine } from "../../../context";
import { imageSignedUrlOptions } from "../../character-extraction/character-extraction.queries";
import type { CharacterBundle, ImageRecord } from "../../character-extraction/character-extraction.types";
import { useCharacterRendering } from "../hooks/useCharacterRendering";

type CharacterBlockProps = {
  bundle: CharacterBundle;
  onRender: () => void;
  isRendering: boolean;
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

function CharacterBlock({ bundle, onRender, isRendering }: CharacterBlockProps) {
  const hasRender = bundle.canonicalRender !== null;

  return (
    <div className={bundle.canonicalRender ? "aspect-square w-full max-w-lg shrink-0" : "h-48 w-full max-w-lg shrink-0"}>
      <div className="relative flex h-full w-full items-center justify-center border border-border bg-muted/20 hover:bg-muted/40">
        {hasRender && <RenderedImage render={bundle.canonicalRender!} />}
        {!hasRender && (
          <span className="text-xs text-muted-foreground">
            {bundle.character.name}
          </span>
        )}
        {hasRender && (
          <span className="absolute bottom-3 left-3 text-xs text-background">
            {bundle.character.name}
          </span>
        )}
        <button
          onClick={onRender}
          disabled={isRendering}
          className="absolute bottom-3 right-3 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
        >
          {isRendering ? "Rendering…" : "Render"}
        </button>
      </div>
    </div>
  );
}

export function CharacterRenderingList({ characters }: { characters: CharacterBundle[] }) {
  const { projectId, storyId } = useSceneEngine();
  const { triggerRender, renderingIds } = useCharacterRendering(projectId, storyId);

  return (
    <div className="flex h-full w-full flex-col items-center gap-2 overflow-y-auto p-4">
      {characters.map((bundle) => (
        <CharacterBlock
          key={bundle.character.id}
          bundle={bundle}
          onRender={() => triggerRender({ characterId: bundle.character.id })}
          isRendering={renderingIds.has(bundle.character.id)}
        />
      ))}
    </div>
  );
}
