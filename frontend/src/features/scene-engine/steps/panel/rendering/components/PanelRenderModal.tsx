import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ModalShell } from "@scene-engine/components/ModalShell";
import PromptInput from "@scene-engine/components/PromptInput";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { useSceneEngine } from "@scene-engine/context";
import type { PanelBundle } from "../../panel.types";
import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";
import { panelRendersOptions } from "../rendering.queries";
import { usePanelRendering } from "../hooks/usePanelRendering";
import { Carousel } from "./Carousel";

type PanelRenderModalProps = {
  bundle: PanelBundle;
  displayIndex: number;
  onDismiss: () => void;
};

export function PanelRenderModal({ bundle, displayIndex, onDismiss }: PanelRenderModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const panelId = bundle.panel.id;

  const { uploadReferenceImage, editRender, editingIds, setCanonicalRender, isSettingCanonical } = usePanelRendering(projectId, storyId);
  const isEditing = editingIds.has(panelId);

  const { data: renders, isLoading } = useQuery(
    panelRendersOptions(projectId, storyId, panelId),
  );

  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (!renders) return;
    const idx = renders.findIndex((r: ImageRecord) => r.id === bundle.canonicalRender?.id);
    setSelectedIndex(idx === -1 ? 0 : idx);
  }, [renders, bundle.canonicalRender?.id]);

  const selectedRender = renders?.[selectedIndex];
  const isCanonical = !!selectedRender && selectedRender.id === bundle.canonicalRender?.id;

  const handleSend = async (instruction: string, files: File[]) => {
    if (!renders || renders.length === 0) return;
    const sourceImage = renders[selectedIndex];
    if (!sourceImage) return;

    let referenceImageId: string | undefined;

    if (files.length > 0) {
      const updatedBundle = await uploadReferenceImage({ panelId, file: files[0] });
      referenceImageId = updatedBundle.referenceImages.at(-1)?.id;
    }

    editRender({ panelId, imageId: sourceImage.id, instruction, referenceImageId });
    setSelectedIndex(0);
  };

  const headerActions = (
    <button
      onClick={() => {
        if (!selectedRender || isCanonical) return;
        setCanonicalRender({ panelId, imageId: selectedRender.id });
      }}
      disabled={isCanonical || isSettingCanonical || !selectedRender}
      className={`px-2 py-1 text-[10px] ${
        isCanonical
          ? "bg-foreground text-background"
          : "border border-foreground/30 text-foreground hover:bg-muted/40 disabled:opacity-50"
      }`}
    >
      {isSettingCanonical ? "Setting…" : isCanonical ? "✓ Selected" : "Use this"}
    </button>
  );

  const renderBody = () => {
    if (isLoading) {
      return <Skeleton className="min-h-0 flex-1 w-full" />;
    }
    if (isEditing) {
      return <Skeleton className="min-h-0 flex-1 w-full" label="Editing" showTimer />;
    }
    if (!renders || renders.length === 0) {
      return (
        <div className="flex min-h-0 flex-1 items-center justify-center bg-muted/20">
          <span className="text-xs text-muted-foreground">No renders yet</span>
        </div>
      );
    }
    return (
      <Carousel
        items={renders}
        index={selectedIndex}
        onIndexChange={setSelectedIndex}
      />
    );
  };

  return (
    <ModalShell
      header={`Panel ${displayIndex}`}
      onDismiss={onDismiss}
      headerActions={headerActions}
    >
      {renderBody()}
      <div className="shrink-0 border-t border-border">
        <PromptInput
          onSend={handleSend}
          placeholder={isCanonical ? "Describe an edit…" : "Only the canonical render can be edited"}
          disabled={isEditing || isLoading || !renders || renders.length === 0 || !isCanonical}
          enableUploads
          maxFiles={1}
          acceptedFileTypes="image/*"
          maxFileSizeMb={5}
          enableVoiceTranscription
        />
      </div>
    </ModalShell>
  );
}
