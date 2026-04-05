import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../../components/Skeleton";
import { useSceneEngine } from "../../context";
import { charactersOptions } from "../character-extraction/character-extraction.queries";
import { CharacterRenderingList } from "./components/CharacterRenderingList";
import { NoCharactersState } from "./components/EmptyState";

export default function CharacterRenderingStep() {
  const { projectId, storyId } = useSceneEngine();
  const { data: characters, isLoading } = useQuery(
    charactersOptions(projectId, storyId),
  );

  if (isLoading) {
    return (
      <div className="flex h-full w-full flex-col gap-2 p-4">
        <Skeleton className="min-h-0 flex-1 w-full" />
        <Skeleton className="min-h-0 flex-1 w-full" />
        <Skeleton className="min-h-0 flex-1 w-full" />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      {characters && characters.length > 0 ? (
        <CharacterRenderingList characters={characters} />
      ) : (
        <NoCharactersState />
      )}
    </div>
  );
}
