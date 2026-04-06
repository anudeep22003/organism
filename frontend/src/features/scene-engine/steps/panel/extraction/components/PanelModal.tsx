import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
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
  onDeleted: () => void;
};

export function PanelModal({ bundle, displayIndex, onDismiss, onImageClick, onDeleted }: PanelModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const { refinePanel, isRefining, uploadReferenceImage, isUploading, deletePanel, isDeletingPanel } =
    usePanelExtraction(projectId, storyId);

  const panelId = bundle.panel.id;
  const [validationError, setValidationError] = useState<string | null>(null);

  const { triggerPick, inputProps } = useFilePicker({
    accept: "image/*",
    multiple: false,
    onPick: ([file]) => uploadReferenceImage({ panelId, file }),
    onReject: setValidationError,
  });

  const headerActions = (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <button className="border border-destructive/40 px-2 py-1 text-[10px] text-destructive hover:bg-destructive/10 disabled:opacity-50">
          Delete
        </button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Panel {displayIndex}?</AlertDialogTitle>
          <AlertDialogDescription>
            This cannot be undone. The panel and all its renders will be permanently removed.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => deletePanel({ panelId }, { onSuccess: onDeleted })}
            disabled={isDeletingPanel}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeletingPanel ? "Deleting…" : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );

  return (
    <ModalShell header={`Panel ${displayIndex}`} onDismiss={onDismiss} headerActions={headerActions}>
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
