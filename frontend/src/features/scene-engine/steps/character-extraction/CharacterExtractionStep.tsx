import { Skeleton } from "../../components/Skeleton";
import { useSceneEngine } from "../../context";
import { useCharacterExtraction } from "./hooks/useCharacterExtraction";
import { CharacterList } from "./components/CharacterList";

function EmptyState({
  onExtract,
  isExtracting,
  error,
}: {
  onExtract: () => void;
  isExtracting: boolean;
  error: string | null;
}) {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between border border-border p-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium">Extract Characters</span>
            <span
              className={`text-[10px] ${error ? "text-destructive" : "text-muted-foreground"}`}
            >
              {error ??
                "Analyse your story and extract all characters with their visual attributes."}
            </span>
          </div>
          <button
            onClick={onExtract}
            disabled={isExtracting || !!error}
            className="ml-6 shrink-0 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
          >
            {isExtracting ? "Extracting…" : "Extract"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function CharacterExtractionStep() {
  const { projectId, storyId } = useSceneEngine();
  const { characters, isLoading, extractCharacters, isExtracting, extractError } =
    useCharacterExtraction(projectId, storyId);

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
        <CharacterList characters={characters} />
      ) : (
        <EmptyState
          onExtract={extractCharacters}
          isExtracting={isExtracting}
          error={extractError}
        />
      )}
    </div>
  );
}
