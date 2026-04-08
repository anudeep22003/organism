type NewStoryModalProps = {
  projectId: string;
  onDismiss: () => void;
};

export function NewStoryModal({ onDismiss }: NewStoryModalProps) {
  return (
    <div className="absolute inset-0 z-20 flex flex-col bg-background">
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <span className="text-sm font-medium">New Story</span>
        <button
          onClick={onDismiss}
          className="bg-foreground px-2 py-1 text-xs text-background hover:bg-foreground/80"
        >
          ✕
        </button>
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <span className="text-xs text-muted-foreground">Coming soon…</span>
      </div>
    </div>
  );
}
