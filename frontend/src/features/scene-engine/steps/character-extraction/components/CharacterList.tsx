import type { CharacterBundle } from "../character-extraction.types";
import { CharacterCard } from "./CharacterCard";

type CharacterListProps = {
  characters: CharacterBundle[];
  onActivate: (characterId: string) => void;
};

export function CharacterList({ characters, onActivate }: CharacterListProps) {
  return (
    <div className="flex h-full w-full flex-col gap-2 overflow-y-auto p-4">
      {characters.map((bundle) => (
        <CharacterCard
          key={bundle.character.id}
          bundle={bundle}
          onActivate={() => onActivate(bundle.character.id)}
        />
      ))}
    </div>
  );
}
