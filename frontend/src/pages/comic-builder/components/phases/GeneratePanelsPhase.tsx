import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useState } from "react";
import { selectPanels } from "../../slices/comicSlice";
import { generatePanels } from "../../slices/thunks/panelThunks";
import { PanelCard } from "../PanelCard";

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
