import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ModalShell } from "../../../components/ModalShell";
import PromptInput from "../../../components/PromptInput";
import { Skeleton } from "../../../components/Skeleton";
import { useSceneEngine } from "../../../context";
import type { CharacterBundle } from "../../character-extraction/character-extraction.types";
import { characterRendersOptions } from "../character-rendering.queries";
import { useCharacterRendering } from "../hooks/useCharacterRendering";
import { Carousel } from "./Carousel";

type CharacterRenderModalProps = {
  bundle: CharacterBundle;
  onDismiss: () => void;
};

export function CharacterRenderModal({ bundle, onDismiss }: CharacterRenderModalProps) {
  const { projectId, storyId } = useSceneEngine();
  const characterId = bundle.character.id;

  const { editRender, editingIds } = useCharacterRendering(projectId, storyId);
  const isEditing = editingIds.has(characterId);

  const { data: renders, isLoading } = useQuery(
    characterRendersOptions(projectId, storyId, characterId),
  );

  const [selectedIndex, setSelectedIndex] = useState(0);

  const isCanonical = false;

  const handleSend = (instruction: string) => {
    if (!renders || renders.length === 0) return;
    const sourceImage = renders[selectedIndex];
    if (!sourceImage) return;
    editRender({ characterId, imageId: sourceImage.id, instruction });
  };

  const headerActions = (
    <button
      disabled
      className={`px-2 py-1 text-[10px] ${
        isCanonical
          ? "bg-foreground text-background hover:bg-foreground/80"
          : "border border-foreground/30 text-foreground hover:bg-muted/40"
      }`}
    >
      {isCanonical ? "✓ Selected" : "Use this"}
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
        onIndexChange={setSelectedIndex}
        initialIndex={0}
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
          showUpload={false}
          placeholder={selectedIndex === 0 ? "Describe an edit…" : "Only the most recent render can be edited"}
          disabled={isEditing || isLoading || !renders || renders.length === 0 || selectedIndex !== 0}
        />
      </div>
    </ModalShell>
  );
}
