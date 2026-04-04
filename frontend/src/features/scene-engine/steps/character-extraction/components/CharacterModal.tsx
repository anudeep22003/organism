import { ModalShell } from "../../../components/ModalShell";
import PromptInput from "../../../components/PromptInput";
import { useSceneEngine } from "../../../context";
import { CharacterAttributes } from "../CharacterAttributes";
import type { CharacterBundle } from "../character-extraction.types";
import { useCharacterExtraction } from "../hooks/useCharacterExtraction";
import { RefImageTray } from "./RefImageTray";

type CharacterModalProps = {
  bundle: CharacterBundle;
  onDismiss: () => void;
  onImageClick: (imageId: string) => void;
};

export function CharacterModal({ bundle, onDismiss, onImageClick }: CharacterModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const { refineCharacter, isRefining, uploadReferenceImage, isUploading } =
    useCharacterExtraction(projectId, storyId);

  const characterId = bundle.character.id;

  return (
    <ModalShell header={bundle.character.name} onDismiss={onDismiss}>
      <div className="flex min-h-0 flex-1">
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <CharacterAttributes character={bundle.character} />
        </div>
        <RefImageTray
          images={bundle.referenceImages}
          variant="modal"
          onImageClick={onImageClick}
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
