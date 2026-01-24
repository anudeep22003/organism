import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useState } from "react";
import { selectPanels } from "../../slices/comicSlice";
import { generatePanels } from "../../slices/thunks/panelThunks";
import type { ComicPanel } from "../../types/consolidatedState";

type PanelCardProps = {
  panel: ComicPanel;
  index: number;
};

const PanelCard = ({ panel, index }: PanelCardProps) => {
  return (
    <div className="flex-shrink-0 w-80 snap-center border border-neutral-300 bg-white">
      {/* Panel number header */}
      <div className="bg-neutral-900 text-white px-3 py-1 text-sm font-medium">
        Panel {index + 1}
      </div>

      {/* Render placeholder or image */}
      <div className="aspect-square bg-neutral-100 flex items-center justify-center border-b border-neutral-200">
        {panel.render?.url ? (
          <img
            src={panel.render.url}
            alt={`Panel ${index + 1}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-neutral-400 text-sm">
            Render not yet generated
          </span>
        )}
      </div>

      {/* Panel details */}
      <div className="p-3 space-y-2 text-sm">
        <div>
          <span className="font-medium text-neutral-900">
            Background:{" "}
          </span>
          <span className="text-neutral-600">{panel.background}</span>
        </div>

        <div>
          <span className="font-medium text-neutral-900">
            Characters:{" "}
          </span>
          <span className="text-neutral-600">
            {panel.characters.join(", ") || "None"}
          </span>
        </div>

        <div>
          <span className="font-medium text-neutral-900">
            Dialogue:{" "}
          </span>
          <span className="text-neutral-600 italic">
            {panel.dialogue || "—"}
          </span>
        </div>
      </div>
    </div>
  );
};

const EmptyState = () => (
  <div className="flex items-center justify-center h-64 border border-dashed border-neutral-300 rounded-md">
    <p className="text-neutral-500 text-sm">
      No panels generated yet. Click the button above to generate panels
      from your story.
    </p>
  </div>
);

const GeneratePanelsPhase = () => {
  const dispatch = useAppDispatch();
  const panels = useAppSelector(selectPanels);
  const projectId = useAppSelector((state) => state.comic.projectId);
  const [isGenerating, setIsGenerating] = useState(false);

  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  const handleGeneratePanels = async () => {
    setIsGenerating(true);
    try {
      await dispatch(generatePanels(projectId)).unwrap();
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="w-full max-w-6xl px-4 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-black">
          Comic Panels
        </h2>
        <Button
          onClick={handleGeneratePanels}
          disabled={isGenerating}
          variant="outline"
          className="border-black text-black hover:bg-neutral-100"
        >
          {isGenerating ? "Generating..." : "Generate Panels"}
        </Button>
      </div>

      {panels.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 snap-x snap-mandatory">
            {panels.map((panel, index) => (
              <PanelCard key={panel.id} panel={panel} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneratePanelsPhase;

