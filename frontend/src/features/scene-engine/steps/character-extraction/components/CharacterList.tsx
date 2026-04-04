import { useState } from "react";
import type { CharacterBundle } from "../character-extraction.types";
import { CharacterCard } from "./CharacterCard";
import { CharacterModal } from "./CharacterModal";

type CharacterListProps = {
  characters: CharacterBundle[];
};

export function CharacterList({ characters }: CharacterListProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const activeBundle = activeId
    ? characters.find((b) => b.character.id === activeId)
    : null;

  return (
    <div className="relative flex h-full w-full flex-col gap-2 overflow-y-auto p-4">
      {activeBundle && (
        <>
          <div className="absolute inset-0 z-10 backdrop-blur-sm pointer-events-none" />
          <CharacterModal
            bundle={activeBundle}
            onDismiss={() => setActiveId(null)}
          />
        </>
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
