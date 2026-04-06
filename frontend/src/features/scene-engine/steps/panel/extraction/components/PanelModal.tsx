import { useState } from "react";
import { ModalShell } from "@scene-engine/components/ModalShell";
import PromptInput from "@scene-engine/components/PromptInput";
import { ValidationErrorBlock } from "@scene-engine/components/ValidationErrorBlock";
import { useSceneEngine } from "@scene-engine/context";
import { useFilePicker } from "@scene-engine/hooks/useFilePicker";
import type { PanelBundle } from "../../panel.types";
import { usePanelExtraction } from "../hooks/usePanelExtraction";
import { PanelAttributes } from "./PanelAttributes";
import { RefImageTray } from "./RefImageTray";

type PanelModalProps = {
  bundle: PanelBundle;
  displayIndex: number;
  onDismiss: () => void;
  onImageClick: (imageId: string) => void;
};

export function PanelModal({ bundle, displayIndex, onDismiss, onImageClick }: PanelModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const { refinePanel, isRefining, uploadReferenceImage, isUploading } =
    usePanelExtraction(projectId, storyId);

  const panelId = bundle.panel.id;
  const [validationError, setValidationError] = useState<string | null>(null);

  const { triggerPick, inputProps } = useFilePicker({
    accept: "image/*",
    multiple: false,
    onPick: ([file]) => uploadReferenceImage({ panelId, file }),
    onReject: setValidationError,
  });

  return (
    <ModalShell header={`Panel ${displayIndex}`} onDismiss={onDismiss}>
      <div className="flex min-h-0 flex-1">
        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <PanelAttributes panel={bundle.panel} />
        </div>
        <RefImageTray
          images={bundle.referenceImages}
          variant="modal"
          onImageClick={onImageClick}
        />
      </div>
      <div className="shrink-0">
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
          onSend={(instruction) => refinePanel({ panelId, instruction })}
          placeholder="Refine this panel…"
          disabled={isRefining}
          enableVoiceTranscription
        />
      </div>
    </ModalShell>
  );
}
