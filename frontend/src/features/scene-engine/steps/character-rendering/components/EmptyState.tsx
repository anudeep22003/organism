import type { CharacterBundle } from "../../character-extraction/character-extraction.types";

/** Shown when no characters have been extracted yet — this step cannot proceed. */
export function NoCharactersState() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="w-full max-w-4xl">
        <div className="flex items-center border border-border p-4">
          <span className="text-[10px] text-muted-foreground">
            Complete Character Extraction first to enable this step.
          </span>
        </div>
      </div>
    </div>
  );
}

type CharacterBlockProps = {
  bundle: CharacterBundle;
};

function CharacterBlock({ bundle }: CharacterBlockProps) {
  return (
    <div className="flex min-h-0 flex-1">
      <div className="relative flex w-full items-center justify-center border border-border bg-muted/20 hover:bg-muted/40">
        <span className="text-xs text-muted-foreground">
          {bundle.character.name}
        </span>
        <button
          disabled
          className="absolute bottom-3 right-3 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
        >
          Render
        </button>
      </div>
    </div>
  );
}

type CharactersAvailableEmptyStateProps = {
  characters: CharacterBundle[];
};

/** Shown when characters are available but none have been rendered yet. */
export function CharactersAvailableEmptyState({
  characters,
}: CharactersAvailableEmptyStateProps) {
  return (
    <div className="flex h-full w-full flex-col gap-2 p-4">
      {characters.map((bundle) => (
        <CharacterBlock key={bundle.character.id} bundle={bundle} />
      ))}
    </div>
  );
}
