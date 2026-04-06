import { useState } from "react";
import { StepLoadingSkeleton } from "@scene-engine/components/StepLoadingSkeleton";
import { useSceneEngine } from "@scene-engine/context";
import { usePanelExtraction } from "./hooks/usePanelExtraction";
import { PanelList } from "./components/PanelList";
import { PanelModal } from "./components/PanelModal";
import { ReferenceImageViewer } from "./components/ReferenceImageViewer";

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
            <span className="text-xs font-medium">Extract Panels</span>
            <span
              className={`text-[10px] ${error ? "text-destructive" : "text-muted-foreground"}`}
            >
              {error ??
                "Analyse your story and extract all panels with their scene descriptions."}
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

export default function PanelExtractionStep() {
  const { projectId, storyId } = useSceneEngine();
  const {
    panels, isLoading,
    extractPanels, isExtracting, extractError,
    deleteReferenceImage, isDeleting,
  } = usePanelExtraction(projectId, storyId);

  const [activeId, setActiveId] = useState<string | null>(null);
  const [viewingImageId, setViewingImageId] = useState<string | null>(null);

  const activeBundle = activeId
    ? panels?.find((b) => b.panel.id === activeId)
    : null;

  const activeIndex = activeId
    ? (panels?.findIndex((b) => b.panel.id === activeId) ?? -1) + 1
    : 0;

  const viewingImage = activeBundle && viewingImageId
    ? activeBundle.referenceImages.find((r) => r.id === viewingImageId)
    : null;

  const handleDelete = () => {
    if (!activeId || !viewingImageId) return;
    deleteReferenceImage(
      { panelId: activeId, imageId: viewingImageId },
      { onSuccess: () => setViewingImageId(null) },
    );
  };

  if (isLoading) {
    return <StepLoadingSkeleton />;
  }

  return (
    <div className="relative flex h-full w-full flex-col">
      {activeBundle && (
        <PanelModal
          bundle={activeBundle}
          displayIndex={activeIndex}
          onDismiss={() => { setActiveId(null); setViewingImageId(null); }}
          onImageClick={setViewingImageId}
          onDeleted={() => { setActiveId(null); setViewingImageId(null); }}
        />
      )}
      {viewingImage && (
        <ReferenceImageViewer
          img={viewingImage}
          onBack={() => setViewingImageId(null)}
          onDelete={handleDelete}
          isDeleting={isDeleting}
        />
      )}
      {panels && panels.length > 0 ? (
        <PanelList panels={panels} onActivate={setActiveId} />
      ) : (
        <EmptyState
          onExtract={extractPanels}
          isExtracting={isExtracting}
          error={extractError}
        />
      )}
    </div>
  );
}
