import { Button } from "@/components/ui/button";
import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import { useSelector } from "react-redux";
import type { Character } from "../types/consolidatedState";
import { CharacterCard } from "./ExtractCharactersPhase";

const dummyApiCall = async () => {
  const response = await httpClient.get<{ message: string }>(
    "/api/comic-builder/phase/dummy"
  );
  console.log(response.message);
  return response;
};

const EmptyImage = () => {
  return (
    <div className="flex bg-green-100 grow items-center justify-center">
      <p>No image generated yet</p>
    </div>
  );
};

const CharacterCardWithImage = ({
  character,
  onGenerateCharacter,
}: {
  character: Character;
  onGenerateCharacter: () => void;
}) => {
  return (
    <div className="flex w-full gap-4">
      <div className="flex flex-col w-1/2">
        <CharacterCard character={character} />
        <Button onClick={onGenerateCharacter}>
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

  const handleGenerateCharacter = (characterId: string) => {
    console.log(`Generating character ${characterId}`);
  };

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
            onGenerateCharacter={() =>
              handleGenerateCharacter(character.id)
            }
          />
        ))}
      </div>
      <Button onClick={dummyApiCall}>Generate Characters</Button>
    </div>
  );
};

export default GenerateCharacterPhase;
