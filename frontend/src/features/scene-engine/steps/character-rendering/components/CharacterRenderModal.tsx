import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ModalShell } from "../../../components/ModalShell";
import PromptInput from "../../../components/PromptInput";
import { Skeleton } from "../../../components/Skeleton";
import { useSceneEngine } from "../../../context";
import { imageSignedUrlOptions } from "../../character-extraction/character-extraction.queries";
import type { CharacterBundle } from "../../character-extraction/character-extraction.types";

type CanonicalRenderViewProps = {
  bundle: CharacterBundle;
};

function CanonicalRenderView({ bundle }: CanonicalRenderViewProps) {
  const queryClient = useQueryClient();
  const render = bundle.canonicalRender;

  const { data } = useQuery(
    imageSignedUrlOptions(render?.id ?? ""),
  );

  if (!render) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center bg-muted/20">
        <span className="text-xs text-muted-foreground">No renders yet</span>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 items-center justify-center bg-muted/20">
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

type CharacterRenderModalProps = {
  bundle: CharacterBundle;
  onDismiss: () => void;
};

export function CharacterRenderModal({ bundle, onDismiss }: CharacterRenderModalProps) {
  const { projectId, storyId } = useSceneEngine();
  void projectId;
  void storyId;

  const isCanonical = false;

  const headerActions = (
    <button
      disabled
      className={`px-2 py-1 text-[10px] ${
        isCanonical
          ? "bg-foreground text-background hover:bg-foreground/80"
          : "border border-foreground/30 text-foreground hover:bg-muted/40"
      }`}
    >
      {isCanonical ? "✓ Selected" : "Use this"}
    </button>
  );

  return (
    <ModalShell
      header={bundle.character.name}
      onDismiss={onDismiss}
      headerActions={headerActions}
    >
      <CanonicalRenderView bundle={bundle} />
      <div className="shrink-0 border-t border-border">
        <PromptInput
          onSend={() => {}}
          showUpload={false}
          placeholder="Describe a new render…"
          disabled
        />
      </div>
    </ModalShell>
  );
}
