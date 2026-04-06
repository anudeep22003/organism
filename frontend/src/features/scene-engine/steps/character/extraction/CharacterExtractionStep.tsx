import { useState } from "react";
import { StepLoadingSkeleton } from "@scene-engine/components/StepLoadingSkeleton";
import { useSceneEngine } from "@scene-engine/context";
import { useCharacterExtraction } from "./hooks/useCharacterExtraction";
import { CharacterList } from "./components/CharacterList";
import { CharacterModal } from "./components/CharacterModal";
import { ReferenceImageViewer } from "./components/ReferenceImageViewer";

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

export default function CharacterExtractionStep() {
  const { projectId, storyId } = useSceneEngine();
  const {
    characters, isLoading,
    extractCharacters, isExtracting, extractError,
    deleteReferenceImage, isDeleting,
  } = useCharacterExtraction(projectId, storyId);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [viewingImageId, setViewingImageId] = useState<string | null>(null);

  const activeBundle = activeId
    ? characters?.find((b) => b.character.id === activeId)
    : null;

  const viewingImage = activeBundle && viewingImageId
    ? activeBundle.referenceImages.find((r) => r.id === viewingImageId)
    : null;

  const handleDelete = () => {
    if (!activeId || !viewingImageId) return;
    deleteReferenceImage(
      { characterId: activeId, imageId: viewingImageId },
      { onSuccess: () => setViewingImageId(null) },
    );
  };

  if (isLoading) {
    return <StepLoadingSkeleton />;
  }

  return (
    <div className="relative flex h-full w-full flex-col">
      {activeBundle && (
        <CharacterModal
          bundle={activeBundle}
          onDismiss={() => { setActiveId(null); setViewingImageId(null); }}
          onImageClick={setViewingImageId}
        />
      )}
      {viewingImage && (
        <ReferenceImageViewer
          img={viewingImage}
          onBack={() => setViewingImageId(null)}
          onDelete={handleDelete}
          isDeleting={isDeleting}
        />
      )}
      {characters && characters.length > 0 ? (
        <CharacterList characters={characters} onActivate={setActiveId} />
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
