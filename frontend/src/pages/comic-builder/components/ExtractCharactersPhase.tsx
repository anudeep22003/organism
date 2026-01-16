import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useParams } from "react-router";
import { selectCharacters } from "../slices/comicSlice";
import { extractCharacters } from "../slices/thunks/characterThunks";
import type { Character } from "../types/consolidatedState";

const formatKey = (key: string): string => {
  // Convert camelCase to Title Case with spaces
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

type CharacterCardProps = {
  character: Character;
};

const CharacterCard = ({ character }: CharacterCardProps) => {
  // Display fields in a readable order, excluding internal fields
  const displayFields: (keyof Character)[] = [
    "name",
    "brief",
    "characterType",
    "role",
    "era",
    "visualForm",
    "colorPalette",
    "distinctiveMarkers",
    "demeanor",
  ];

  return (
    <div className="border border-neutral-200 bg-white p-4 space-y-2">
      {displayFields.map((key) => {
        const value = character[key];
        if (value === null || value === undefined) return null;
        return (
          <div key={key} className="text-sm">
            <span className="font-medium text-neutral-900">
              {formatKey(key)}:{" "}
            </span>
            <span className="text-neutral-600">{String(value)}</span>
          </div>
        );
      })}
    </div>
  );
};

const ExtractCharactersPhase = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();
  const characters = useAppSelector(selectCharacters);

  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  const characterList = Object.values(characters);

  const handleExtractCharactersClick = () => {
    dispatch(extractCharacters(projectId));
  };

  return (
    <div className="w-full max-w-4xl px-4 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-black">Characters</h2>
        <Button
          onClick={handleExtractCharactersClick}
          variant="outline"
          className="border-black text-black hover:bg-neutral-100"
        >
          Extract Characters
        </Button>
      </div>

      {characterList.length === 0 ? (
        <p className="text-neutral-500 text-sm">
          No characters extracted yet. Click the button above to extract
          characters from your story.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {characterList.map((character) => (
            <CharacterCard key={character.id} character={character} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ExtractCharactersPhase;
