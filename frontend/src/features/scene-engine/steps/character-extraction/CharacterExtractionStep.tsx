import { useSceneEngine } from "../../context";
import { useCharacterExtraction } from "./hooks/useCharacterExtraction";

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

function CharacterList({ characters }: { characters: Record<string, unknown>[] }) {
  return (
    <div className="flex h-full w-full flex-col gap-2 overflow-y-auto p-4">
      {characters.map((character, i) => (
        <div key={(character.id as string) ?? i} className="border border-border bg-muted/20 p-3">
          <pre className="whitespace-pre-wrap text-[10px] text-muted-foreground">
            {JSON.stringify(character, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  );
}

export default function CharacterExtractionStep() {
  const { projectId, storyId } = useSceneEngine();
  const { characters, extractCharacters, isExtracting, extractError } =
    useCharacterExtraction(projectId, storyId);

  const hasCharacters = !!characters?.length;

  return (
    <div className="flex h-full w-full flex-col">
      {hasCharacters ? (
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
