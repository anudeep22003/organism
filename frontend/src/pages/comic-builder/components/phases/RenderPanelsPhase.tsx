import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useEffect, useState } from "react";
import { selectPanels } from "../../slices/comicSlice";
import {
  renderAllPanels,
  renderPanel,
} from "../../slices/thunks/panelThunks";
import type { ComicPanel } from "../../types/consolidatedState";
import { PanelCard } from "../PanelCard";

type PanelCardWithRenderProps = {
  panel: ComicPanel;
  index: number;
  projectId: string;
  isBulkRendering: boolean;
};

const PanelCardWithRender = ({
  panel,
  index,
  projectId,
  isBulkRendering,
}: PanelCardWithRenderProps) => {
  const dispatch = useAppDispatch();
  const [isRendering, setIsRendering] = useState(false);

  const isUnrendered = !panel.render?.url;
  const isBulkRenderingThisPanel = isBulkRendering && isUnrendered;
  const isDisabled = isRendering || isBulkRenderingThisPanel;

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

  const getButtonText = () => {
    if (isRendering || isBulkRenderingThisPanel) return "Rendering...";
    return "Render Panel";
  };

  return (
    <div className="flex flex-col gap-2">
      <PanelCard panel={panel} index={index} />
      <Button
        onClick={handleRenderPanel}
        disabled={isDisabled}
        variant="outline"
        className="border-black text-black hover:bg-neutral-100"
      >
        {getButtonText()}
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
  const dispatch = useAppDispatch();
  const panels = useAppSelector(selectPanels);
  const projectId = useAppSelector((state) => state.comic.projectId);
  const [isRenderingAll, setIsRenderingAll] = useState(false);

  const unrenderedPanels = panels.filter((p) => !p.render?.url);
  const hasUnrenderedPanels = unrenderedPanels.length > 0;

  const handleRenderAllPanels = async () => {
    if (!projectId) return;
    setIsRenderingAll(true);
    try {
      await dispatch(renderAllPanels(projectId)).unwrap();
    } catch (error) {
      console.error("Failed to render all panels:", error);
    } finally {
      // setIsRenderingAll(false);
    }
  };

  useEffect(() => {
    if (!hasUnrenderedPanels) {
      setIsRenderingAll(false);
    }
  }, [hasUnrenderedPanels]);

  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  return (
    <div className="w-full max-w-6xl px-4 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-black">
          Render Panels
        </h2>
        {panels.length > 0 && (
          <Button
            onClick={handleRenderAllPanels}
            disabled={isRenderingAll || !hasUnrenderedPanels}
            className="bg-black text-white hover:bg-neutral-800"
          >
            {isRenderingAll ? "Rendering All..." : "Render All Panels"}
          </Button>
        )}
      </div>

      {panels.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {panels.map((panel, index) => (
            <PanelCardWithRender
              key={panel.id}
              panel={panel}
              index={index}
              projectId={projectId}
              isBulkRendering={isRenderingAll}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default RenderPanelsPhase;
