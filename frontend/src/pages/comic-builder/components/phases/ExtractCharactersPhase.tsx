import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { selectCharacters } from "../../slices/comicSlice";
import { extractCharacters } from "../../slices/thunks/characterThunks";
import { CharacterCard } from "../CharacterCard";

const ExtractCharactersPhase = () => {
  const dispatch = useAppDispatch();
  const projectId = useAppSelector((state) => state.comic.projectId);
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
