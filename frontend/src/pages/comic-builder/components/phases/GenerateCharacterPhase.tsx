import { Button } from "@/components/ui/button";
import type { RootState } from "@/store";
import { useAppDispatch } from "@/store/hooks";
import { useSelector } from "react-redux";
import { renderCharacter } from "../../slices/thunks/characterThunks";
import type { Character } from "../../types/consolidatedState";
import { CharacterCard } from "../CharacterCard";

const EmptyImage = () => {
  return (
    <div className="flex bg-green-100 grow items-center justify-center">
      <p>No image generated yet</p>
    </div>
  );
};

const CharacterCardWithImage = ({
  character,
  projectId,
}: {
  character: Character;
  projectId: string;
}) => {
  const dispatch = useAppDispatch();

  const handleGenerateCharacter = () => {
    dispatch(renderCharacter({ projectId, character }));
  };

  return (
    <div className="flex w-full gap-4">
      <div className="flex flex-col w-1/2">
        <CharacterCard character={character} />
        <Button onClick={handleGenerateCharacter}>
          Generate Character
        </Button>
      </div>
      {character.render ? (
        <img
          src={character.render.url ?? ""}
          alt={character.name}
          className="w-full h-auto"
        />
      ) : (
        <EmptyImage />
      )}
    </div>
  );
};

const GenerateCharacterPhase = () => {
  const characters = useSelector(
    (state: RootState) => state.comic.characters
  );
  const projectId = useSelector(
    (state: RootState) => state.comic.projectId
  );

  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  return (
    <div className="w-full max-w-4xl px-4 space-y-6">
      <h2 className="text-xl font-semibold text-black">
        Generate Characters
      </h2>
      <div className="flex flex-col gap-4">
        {Object.values(characters).map((character) => (
          <CharacterCardWithImage
            key={character.id}
            character={character}
            projectId={projectId}
          />
        ))}
      </div>
    </div>
  );
};

export default GenerateCharacterPhase;

