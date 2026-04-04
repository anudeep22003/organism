import { useState } from "react";
import { ModalShell } from "../../../components/ModalShell";
import PromptInput from "../../../components/PromptInput";
import { useSceneEngine } from "../../../context";
import { CharacterAttributes } from "../CharacterAttributes";
import type { CharacterBundle } from "../character-extraction.types";
import { useCharacterExtraction } from "../hooks/useCharacterExtraction";
import { RefImageTray } from "./RefImageTray";
import { ReferenceImageViewer } from "./ReferenceImageViewer";

type CharacterModalProps = {
  bundle: CharacterBundle;
  onDismiss: () => void;
};

export function CharacterModal({ bundle, onDismiss }: CharacterModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const {
    refineCharacter,
    isRefining,
    uploadReferenceImage,
    isUploading,
    deleteReferenceImage,
    isDeleting,
  } = useCharacterExtraction(projectId, storyId);

  const [viewingImageId, setViewingImageId] = useState<string | null>(null);
  const characterId = bundle.character.id;

  const viewingImage = viewingImageId
    ? bundle.referenceImages.find((r) => r.id === viewingImageId)
    : null;

  const handleDelete = () => {
    if (!viewingImageId) return;
    deleteReferenceImage(
      { characterId, imageId: viewingImageId },
      { onSuccess: () => setViewingImageId(null) },
    );
  };

  return (
    <ModalShell header={bundle.character.name} onDismiss={onDismiss}>
      {viewingImage && (
        <ReferenceImageViewer
          img={viewingImage}
          onBack={() => setViewingImageId(null)}
          onDelete={handleDelete}
          isDeleting={isDeleting}
        />
      )}

      <div className="flex min-h-0 flex-1">
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <CharacterAttributes character={bundle.character} />
        </div>
        <RefImageTray
          images={bundle.referenceImages}
          variant="modal"
          onImageClick={setViewingImageId}
        />
      </div>
      <div className="shrink-0 border-t border-border">
        <PromptInput
          onSend={(instruction) => refineCharacter({ characterId, instruction })}
          onUpload={(files) =>
            files.forEach((file) => uploadReferenceImage({ characterId, file }))
          }
          showUpload={true}
          acceptedFileTypes="image/*"
          placeholder="Refine this character…"
          disabled={isRefining || isUploading}
        />
      </div>
    </ModalShell>
  );
}
