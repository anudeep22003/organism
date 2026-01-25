import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useState } from "react";
import { selectPanels } from "../../slices/comicSlice";
import { renderPanel } from "../../slices/thunks/panelThunks";
import type { ComicPanel } from "../../types/consolidatedState";
import { PanelCard } from "../PanelCard";

type PanelCardWithRenderProps = {
  panel: ComicPanel;
  index: number;
  projectId: string;
};

const PanelCardWithRender = ({
  panel,
  index,
  projectId,
}: PanelCardWithRenderProps) => {
  const dispatch = useAppDispatch();
  const [isRendering, setIsRendering] = useState(false);

  const handleRenderPanel = async () => {
    setIsRendering(true);
    try {
      await dispatch(renderPanel({ projectId, panel })).unwrap();
    } catch (error) {
      console.error("Failed to render panel:", error);
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="flex-shrink-0 w-80 snap-center flex flex-col gap-2">
      <PanelCard panel={panel} index={index} />
      <Button
        onClick={handleRenderPanel}
        disabled={isRendering}
        variant="outline"
        className="border-black text-black hover:bg-neutral-100"
      >
        {isRendering ? "Rendering..." : "Render Panel"}
      </Button>
    </div>
  );
};

const EmptyState = () => (
  <div className="flex items-center justify-center h-64 border border-dashed border-neutral-300 rounded-md">
    <p className="text-neutral-500 text-sm">
      No panels available. Generate panels in the previous step first.
    </p>
  </div>
);

const RenderPanelsPhase = () => {
  const panels = useAppSelector(selectPanels);
  const projectId = useAppSelector((state) => state.comic.projectId);

  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  return (
    <div className="w-full max-w-6xl px-4 space-y-6">
      <h2 className="text-xl font-semibold text-black">
        Render Panels
      </h2>

      {panels.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 snap-x snap-mandatory">
            {panels.map((panel, index) => (
              <PanelCardWithRender
                key={panel.id}
                panel={panel}
                index={index}
                projectId={projectId}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RenderPanelsPhase;
