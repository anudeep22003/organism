import { useState } from "react";
import { ModalShell } from "../../../components/ModalShell";
import PromptInput from "../../../components/PromptInput";
import { ValidationErrorBlock } from "../../../components/ValidationErrorBlock";
import { useSceneEngine } from "../../../context";
import { useFilePicker } from "../../../hooks/useFilePicker";
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
  const [validationError, setValidationError] = useState<string | null>(null);

  const { triggerPick, inputProps } = useFilePicker({
    accept: "image/*",
    multiple: false,
    onPick: ([file]) => uploadReferenceImage({ characterId, file }),
    onReject: setValidationError,
  });

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
        {validationError && (
          <ValidationErrorBlock
            message={validationError}
            onClear={() => setValidationError(null)}
          />
        )}
        <div className="px-3 py-2">
          <input {...inputProps} />
          <button
            onClick={triggerPick}
            disabled={isUploading}
            className="bg-foreground px-2 py-1 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
          >
            {isUploading ? "Uploading…" : "Upload a reference image"}
          </button>
        </div>
      </div>
      <div className="shrink-0 border-t border-border">
        <PromptInput
          onSend={(instruction) => refineCharacter({ characterId, instruction })}
          placeholder="Refine this character…"
          disabled={isRefining}
          enableVoiceTranscription
        />
      </div>
    </ModalShell>
  );
}
