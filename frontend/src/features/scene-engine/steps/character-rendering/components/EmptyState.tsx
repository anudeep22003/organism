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
