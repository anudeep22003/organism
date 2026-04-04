import { useState } from "react";
import { ModalShell } from "../../components/ModalShell";
import PromptInput from "../../components/PromptInput";
import { Skeleton } from "../../components/Skeleton";
import { useSceneEngine } from "../../context";
import { CharacterAttributes } from "./CharacterAttributes";
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

function CharacterModal({
  character,
  onDismiss,
  onRefine,
  isRefining,
}: {
  character: Record<string, unknown>;
  onDismiss: () => void;
  onRefine: (instruction: string) => void;
  isRefining: boolean;
}) {
  const name = (character.name as string) ?? "Character";

  return (
    <ModalShell header={name} onDismiss={onDismiss}>
      <div className="min-h-0 flex-1 overflow-y-auto p-3">
        <CharacterAttributes character={character} />
      </div>
      <div className="shrink-0 border-t border-border">
        <PromptInput
          onSend={onRefine}
          showUpload={false}
          placeholder="Refine this character…"
          disabled={isRefining}
        />
      </div>
    </ModalShell>
  );
}

function CharacterCard({
  character,
  onActivate,
}: {
  character: Record<string, unknown>;
  onActivate: () => void;
}) {
  return (
    <div
      className="border border-border bg-muted/20 p-3 hover:bg-muted/40 cursor-pointer"
      onClick={onActivate}
    >
      <CharacterAttributes character={character} />
    </div>
  );
}

function CharacterList({
  characters,
  refineCharacter,
  isRefining,
}: {
  characters: Record<string, unknown>[];
  refineCharacter: (args: { characterId: string; instruction: string }) => void;
  isRefining: boolean;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const activeCharacter = activeId
    ? characters.find((c) => (c.id as string) === activeId)
    : null;

  return (
    <div className="relative flex h-full w-full flex-col gap-2 overflow-y-auto p-4">
      {activeCharacter && (
        <>
          <div className="absolute inset-0 z-10 backdrop-blur-sm pointer-events-none" />
          <CharacterModal
            character={activeCharacter}
            onDismiss={() => setActiveId(null)}
            onRefine={(instruction) =>
              refineCharacter({ characterId: activeId!, instruction })
            }
            isRefining={isRefining}
          />
        </>
      )}

      {characters.map((character, i) => {
        const id = (character.id as string) ?? String(i);
        return (
          <CharacterCard
            key={id}
            character={character}
            onActivate={() => setActiveId(id)}
          />
        );
      })}
    </div>
  );
}

export default function CharacterExtractionStep() {
  const { projectId, storyId } = useSceneEngine();
  const {
    characters,
    isLoading,
    extractCharacters,
    isExtracting,
    extractError,
    refineCharacter,
    isRefining,
  } = useCharacterExtraction(projectId, storyId);

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
        <CharacterList
          characters={characters}
          refineCharacter={refineCharacter}
          isRefining={isRefining}
        />
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
