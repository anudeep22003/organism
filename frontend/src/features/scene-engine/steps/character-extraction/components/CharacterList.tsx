import { useState } from "react";
import { useSceneEngine } from "../../../context";
import type { CharacterBundle } from "../character-extraction.types";
import { useCharacterExtraction } from "../hooks/useCharacterExtraction";
import { CharacterCard } from "./CharacterCard";
import { CharacterModal } from "./CharacterModal";
import { ReferenceImageViewer } from "./ReferenceImageViewer";

type CharacterListProps = {
  characters: CharacterBundle[];
};

export function CharacterList({ characters }: CharacterListProps) {
  const { projectId, storyId } = useSceneEngine();
  const { deleteReferenceImage, isDeleting } = useCharacterExtraction(projectId, storyId);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [viewingImageId, setViewingImageId] = useState<string | null>(null);

  const activeBundle = activeId
    ? characters.find((b) => b.character.id === activeId)
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

  return (
    <div className="relative flex h-full w-full flex-col gap-2 overflow-y-auto p-4">
      {activeBundle && (
        <>
          <div className="absolute inset-0 z-10 backdrop-blur-sm pointer-events-none" />
          <CharacterModal
            bundle={activeBundle}
            onDismiss={() => { setActiveId(null); setViewingImageId(null); }}
            onImageClick={setViewingImageId}
          />
        </>
      )}

      {viewingImage && (
        <ReferenceImageViewer
          img={viewingImage}
          onBack={() => setViewingImageId(null)}
          onDelete={handleDelete}
          isDeleting={isDeleting}
        />
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
