function EmptyState() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between border border-border p-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium">Extract Characters</span>
            <span className="text-[10px] text-muted-foreground">
              Analyse your story and extract all characters with their visual attributes.
            </span>
          </div>
          <button className="ml-6 shrink-0 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80">
            Extract
          </button>
        </div>
      </div>
    </div>
  );
}

export default function CharacterExtractionStep() {
  return (
    <div className="flex h-full w-full p-4">
      <EmptyState />
    </div>
  );
}
