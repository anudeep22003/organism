import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { StepLoadingSkeleton } from "@scene-engine/components/StepLoadingSkeleton";
import { useSceneEngine } from "@scene-engine/context";
import { panelsOptions } from "../panel/panel.queries";
import { ComicCarousel } from "./components/ComicCarousel";

function NoPanelsState() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="w-full max-w-4xl">
        <div className="flex items-center border border-border p-4">
          <span className="text-[10px] text-muted-foreground">
            Complete Panel Extraction first to enable this step.
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ReviewStep() {
  const { projectId, storyId } = useSceneEngine();
  const { data: panels, isLoading } = useQuery(panelsOptions(projectId, storyId));
  const [index, setIndex] = useState(0);

  if (isLoading) {
    return <StepLoadingSkeleton />;
  }

  if (!panels || panels.length === 0) {
    return <NoPanelsState />;
  }

  return (
    <div className="flex h-full w-full flex-col">
      <ComicCarousel panels={panels} index={index} onIndexChange={setIndex} />
    </div>
  );
}
