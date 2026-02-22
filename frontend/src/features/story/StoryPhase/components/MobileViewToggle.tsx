type ActiveView = "prompt" | "artifact";

type MobileViewToggleProps = {
  activeView: ActiveView;
  onViewChange: (view: ActiveView) => void;
};

function MobileViewToggle({
  activeView,
  onViewChange,
}: MobileViewToggleProps) {
  return (
    <div className="flex items-center justify-center p-2 md:hidden border-b border-border">
      <div className="inline-flex rounded-lg bg-muted border border-border/60 p-0.5">
        <button
          onClick={() => onViewChange("prompt")}
          className={`px-4 py-1.5 text-xs font-medium rounded-md transition-colors ${
            activeView === "prompt"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Prompt
        </button>
        <button
          onClick={() => onViewChange("artifact")}
          className={`px-4 py-1.5 text-xs font-medium rounded-md transition-colors ${
            activeView === "artifact"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Story
        </button>
      </div>
    </div>
  );
}

export default MobileViewToggle;
