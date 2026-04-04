import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ModalShell } from "../../components/ModalShell";
import PromptInput from "../../components/PromptInput";
import { Skeleton } from "../../components/Skeleton";
import { useSceneEngine } from "../../context";
import { CharacterAttributes } from "./CharacterAttributes";
import { imageSignedUrlOptions } from "./character-extraction.queries";
import type { CharacterBundle, ImageRecord } from "./character-extraction.types";
import { useCharacterExtraction } from "./hooks/useCharacterExtraction";

function EmptyState({
  onExtract,
  isExtracting,
  error,
}: {
  onExtract: () => void;
  isExtracting: boolean;
  error: string | null;
}) {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between border border-border p-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium">Extract Characters</span>
            <span
              className={`text-[10px] ${error ? "text-destructive" : "text-muted-foreground"}`}
            >
              {error ??
                "Analyse your story and extract all characters with their visual attributes."}
            </span>
          </div>
          <button
            onClick={onExtract}
            disabled={isExtracting || !!error}
            className="ml-6 shrink-0 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
          >
            {isExtracting ? "Extracting…" : "Extract"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RefImageThumbnail({
  img,
  isLast,
}: {
  img: ImageRecord;
  isLast: boolean;
}) {
  const queryClient = useQueryClient();
  const { data } = useQuery(imageSignedUrlOptions(img.id));

  return (
    <div
      className={`relative aspect-square w-full shrink-0 cursor-pointer bg-muted/20 hover:bg-muted/40 ${
        !isLast ? "border-b border-border" : ""
      }`}
    >
      {data?.url ? (
        <img
          src={data.url}
          alt=""
          className="h-full w-full object-cover"
          onError={() =>
            void queryClient.invalidateQueries({
              queryKey: imageSignedUrlOptions(img.id).queryKey,
            })
          }
        />
      ) : (
        <Skeleton className="h-full w-full" />
      )}
    </div>
  );
}

function RefImageTray({
  images,
  variant,
}: {
  images: ImageRecord[];
  variant: "card" | "modal";
}) {
  const outerClass =
    variant === "card"
      ? `border border-l-0 ${images.length > 0 ? "border-border" : "border-transparent"}`
      : "";

  return (
    <div className={`flex w-16 shrink-0 self-end flex-col overflow-y-auto ${outerClass}`}>
      {images.map((img, i) => (
        <RefImageThumbnail
          key={img.id}
          img={img}
          isLast={i === images.length - 1}
        />
      ))}
    </div>
  );
}

function CharacterModal({
  bundle,
  onDismiss,
  onRefine,
  isRefining,
  onUpload,
  isUploading,
}: {
  bundle: CharacterBundle;
  onDismiss: () => void;
  onRefine: (instruction: string) => void;
  isRefining: boolean;
  onUpload: (file: File) => void;
  isUploading: boolean;
}) {
  return (
    <ModalShell header={bundle.character.name} onDismiss={onDismiss}>
      <div className="flex min-h-0 flex-1">
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <CharacterAttributes character={bundle.character} />
        </div>
        <RefImageTray images={bundle.referenceImages} variant="modal" />
      </div>
      <div className="shrink-0 border-t border-border">
        <PromptInput
          onSend={onRefine}
          onUpload={(files) => files.forEach(onUpload)}
          showUpload={true}
          acceptedFileTypes="image/*"
          placeholder="Refine this character…"
          disabled={isRefining || isUploading}
        />
      </div>
    </ModalShell>
  );
}

function CharacterCard({
  bundle,
  onActivate,
}: {
  bundle: CharacterBundle;
  onActivate: () => void;
}) {
  return (
    <div className="flex" onClick={onActivate}>
      <div className="min-w-0 flex-1 cursor-pointer border border-border bg-muted/20 p-3 hover:bg-muted/40">
        <CharacterAttributes character={bundle.character} />
      </div>
      <RefImageTray images={bundle.referenceImages} variant="card" />
    </div>
  );
}

function CharacterList({
  characters,
  refineCharacter,
  isRefining,
  uploadReferenceImage,
  isUploading,
}: {
  characters: CharacterBundle[];
  refineCharacter: (args: { characterId: string; instruction: string }) => void;
  isRefining: boolean;
  uploadReferenceImage: (args: { characterId: string; file: File }) => void;
  isUploading: boolean;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const activeBundle = activeId
    ? characters.find((b) => b.character.id === activeId)
    : null;

  return (
    <div className="relative flex h-full w-full flex-col gap-2 overflow-y-auto p-4">
      {activeBundle && (
        <>
          <div className="absolute inset-0 z-10 backdrop-blur-sm pointer-events-none" />
          <CharacterModal
            bundle={activeBundle}
            onDismiss={() => setActiveId(null)}
            onRefine={(instruction) =>
              refineCharacter({ characterId: activeId!, instruction })
            }
            isRefining={isRefining}
            onUpload={(file) =>
              uploadReferenceImage({ characterId: activeId!, file })
            }
            isUploading={isUploading}
          />
        </>
      )}

      {characters.map((bundle) => (
        <CharacterCard
          key={bundle.character.id}
          bundle={bundle}
          onActivate={() => setActiveId(bundle.character.id)}
        />
      ))}
    </div>
  );
}

export default function CharacterExtractionStep() {
  const { projectId, storyId } = useSceneEngine();
  const {
    characters,
    isLoading,
    extractCharacters,
    isExtracting,
    extractError,
    refineCharacter,
    isRefining,
    uploadReferenceImage,
    isUploading,
  } = useCharacterExtraction(projectId, storyId);

  if (isLoading) {
    return (
      <div className="flex h-full w-full flex-col gap-2 p-4">
        <Skeleton className="min-h-0 flex-1 w-full" />
        <Skeleton className="min-h-0 flex-1 w-full" />
        <Skeleton className="min-h-0 flex-1 w-full" />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      {characters && characters.length > 0 ? (
        <CharacterList
          characters={characters}
          refineCharacter={refineCharacter}
          isRefining={isRefining}
          uploadReferenceImage={uploadReferenceImage}
          isUploading={isUploading}
        />
      ) : (
        <EmptyState
          onExtract={extractCharacters}
          isExtracting={isExtracting}
          error={extractError}
        />
      )}
    </div>
  );
}
