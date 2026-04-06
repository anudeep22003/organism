import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { StepLoadingSkeleton } from "../../../components/StepLoadingSkeleton";
import { useSceneEngine } from "../../../context";
import { charactersOptions } from "../character.queries";
import { CharacterRenderModal } from "./components/CharacterRenderModal";
import { CharacterRenderingList } from "./components/CharacterRenderingList";
import { NoCharactersState } from "./components/EmptyState";

export default function CharacterRenderingStep() {
  const { projectId, storyId } = useSceneEngine();
  const { data: characters, isLoading } = useQuery(
    charactersOptions(projectId, storyId),
  );

  const [activeId, setActiveId] = useState<string | null>(null);
  const activeBundle = activeId
    ? characters?.find((b) => b.character.id === activeId)
    : null;

  if (isLoading) {
    return <StepLoadingSkeleton />;
  }

  return (
    <div className="relative flex h-full w-full flex-col">
      {activeBundle && (
        <CharacterRenderModal
          bundle={activeBundle}
          onDismiss={() => setActiveId(null)}
        />
      )}
      {characters && characters.length > 0 ? (
        <CharacterRenderingList
          characters={characters}
          onActivate={setActiveId}
        />
      ) : (
        <NoCharactersState />
      )}
    </div>
  );
}
