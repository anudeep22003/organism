import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ModalShell } from "../../../../components/ModalShell";
import PromptInput from "../../../../components/PromptInput";
import { Skeleton } from "../../../../components/Skeleton";
import { useSceneEngine } from "../../../../context";
import type { CharacterBundle } from "../../character.types";
import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";
import { characterRendersOptions } from "../rendering.queries";
import { useCharacterRendering } from "../hooks/useCharacterRendering";
import { Carousel } from "./Carousel";

type CharacterRenderModalProps = {
  bundle: CharacterBundle;
  onDismiss: () => void;
};

export function CharacterRenderModal({ bundle, onDismiss }: CharacterRenderModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const characterId = bundle.character.id;

  const { uploadReferenceImage, editRender, editingIds, setCanonicalRender, isSettingCanonical } = useCharacterRendering(projectId, storyId);
  const isEditing = editingIds.has(characterId);

  const { data: renders, isLoading } = useQuery(
    characterRendersOptions(projectId, storyId, characterId),
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
      const updatedBundle = await uploadReferenceImage({ characterId, file: files[0] });
      referenceImageId = updatedBundle.referenceImages.at(-1)?.id;
    }

    editRender({ characterId, imageId: sourceImage.id, instruction, referenceImageId });
  };

  const headerActions = (
    <button
      onClick={() => {
        if (!selectedRender || isCanonical) return;
        setCanonicalRender({ characterId, imageId: selectedRender.id });
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
    const canonicalIndex = renders.findIndex((r: ImageRecord) => r.id === bundle.canonicalRender?.id);
    return (
      <Carousel
        items={renders}
        onIndexChange={setSelectedIndex}
        initialIndex={canonicalIndex === -1 ? 0 : canonicalIndex}
      />
    );
  };

  return (
    <ModalShell
      header={bundle.character.name}
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
