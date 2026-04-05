import { useQuery } from "@tanstack/react-query";
import { useSceneEngine } from "../../context";
import { charactersOptions } from "../character-extraction/character-extraction.queries";
import { CharactersAvailableEmptyState, NoCharactersState } from "./components/EmptyState";

export default function CharacterRenderingStep() {
  const { projectId, storyId } = useSceneEngine();
  const { data: characters } = useQuery(charactersOptions(projectId, storyId));

  return (
    <div className="flex h-full w-full flex-col">
      {characters && characters.length > 0 ? (
        <CharactersAvailableEmptyState characters={characters} />
      ) : (
        <NoCharactersState />
      )}
    </div>
  );
}
