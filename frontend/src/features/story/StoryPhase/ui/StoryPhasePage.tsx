import { useState } from "react";
import { useParams } from "react-router";
import PromptPanel from "./components/PromptPanel/PromptPanel";
import ArtifactPanel from "./components/ArtifactPanel/ArtifactPanel";
import MobileViewToggle from "./components/MobileViewToggle/MobileViewToggle";
import { useStoryPhase } from "./hooks/useStoryPhase";

type ActiveView = "prompt" | "artifact";

function StoryPhasePage() {
  const { storyId } = useParams();
  const [activeView, setActiveView] = useState<ActiveView>("prompt");
  const { messages, storyText, isGenerating, submitPrompt } =
    useStoryPhase(storyId ?? "");

  return (
    <div className="fixed inset-0 top-[41px]">
      {/* Desktop: side-by-side grid */}
      <div className="hidden md:grid md:grid-cols-[35%_1px_1fr] h-full">
        <PromptPanel
          messages={messages}
          onSubmit={submitPrompt}
          isGenerating={isGenerating}
        />
        <div className="bg-border" />
        <div className="h-full overflow-hidden bg-card/30">
          <ArtifactPanel
            storyText={storyText}
            isStreaming={isGenerating}
          />
        </div>
      </div>

      {/* Mobile: toggled views */}
      <div className="flex flex-col h-full md:hidden">
        <MobileViewToggle
          activeView={activeView}
          onViewChange={setActiveView}
        />
        <div className="flex-1 min-h-0">
          {activeView === "prompt" ? (
            <PromptPanel
              messages={messages}
              onSubmit={submitPrompt}
              isGenerating={isGenerating}
            />
          ) : (
            <div className="h-full bg-card/30">
              <ArtifactPanel
                storyText={storyText}
                isStreaming={isGenerating}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StoryPhasePage;
