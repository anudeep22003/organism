import type { CharacterBundle } from "../../character.types";
import { CharacterCard } from "./CharacterCard";

type CharacterListProps = {
  characters: CharacterBundle[];
  onActivate: (characterId: string) => void;
};

export function CharacterList({ characters, onActivate }: CharacterListProps) {
  return (
    <div className="h-full w-full overflow-y-auto p-4">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-2">
        {characters.map((bundle) => (
          <CharacterCard
            key={bundle.character.id}
            bundle={bundle}
            onActivate={() => onActivate(bundle.character.id)}
          />
        ))}
      </div>
    </div>
  );
}
