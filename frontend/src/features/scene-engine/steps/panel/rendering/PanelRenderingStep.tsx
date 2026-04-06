import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { StepLoadingSkeleton } from "@scene-engine/components/StepLoadingSkeleton";
import { useSceneEngine } from "@scene-engine/context";
import { panelsOptions } from "../panel.queries";
import { PanelRenderModal } from "./components/PanelRenderModal";
import { PanelRenderingList } from "./components/PanelRenderingList";
import { NoPanelsState } from "./components/EmptyState";

export default function PanelRenderingStep() {
  const { projectId, storyId } = useSceneEngine();
  const { data: panels, isLoading } = useQuery(
    panelsOptions(projectId, storyId),
  );

  const [activeId, setActiveId] = useState<string | null>(null);
  const activeBundle = activeId
    ? panels?.find((b) => b.panel.id === activeId)
    : null;

  const activeIndex = activeId
    ? (panels?.findIndex((b) => b.panel.id === activeId) ?? -1) + 1
    : 0;

  if (isLoading) {
    return <StepLoadingSkeleton />;
  }

  return (
    <div className="relative flex h-full w-full flex-col">
      {activeBundle && (
        <PanelRenderModal
          bundle={activeBundle}
          displayIndex={activeIndex}
          onDismiss={() => setActiveId(null)}
        />
      )}
      {panels && panels.length > 0 ? (
        <PanelRenderingList
          panels={panels}
          onActivate={setActiveId}
        />
      ) : (
        <NoPanelsState />
      )}
    </div>
  );
}
