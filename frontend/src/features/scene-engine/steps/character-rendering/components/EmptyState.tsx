export function EmptyState() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between border border-border p-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium">Render Characters</span>
            <span className="text-[10px] text-muted-foreground">
              Generate AI renders for each character in your story.
            </span>
          </div>
          <button
            disabled
            className="ml-6 shrink-0 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
          >
            Render All
          </button>
        </div>
      </div>
    </div>
  );
}
