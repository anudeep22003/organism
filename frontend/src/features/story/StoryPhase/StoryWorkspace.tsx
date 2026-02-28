import { useCallback, useState } from "react";
import { Link, useParams } from "react-router";
import { IconHistory } from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import { ArtifactCard } from "../components/ArtifactCard";
import type { RefinePayload } from "../components/ArtifactCard";
import HistoryOverlay from "../components/HistoryOverlay";
import StoryContent from "../components/StoryContent";
import { useStoryPhase } from "./hooks/useStoryPhase";
import { useStoryHistory } from "./hooks/useStoryHistory";

function StoryWorkspace() {
  const { projectId, storyId } = useParams();
  const pid = projectId ?? "";
  const sid = storyId ?? "";

  const { storyText, userInputText, error, isGenerating, submitPrompt } =
    useStoryPhase(pid, sid);
  const { data: historyEvents } = useStoryHistory(pid, sid);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const handleStoryRefine = useCallback(
    (payload: RefinePayload) => submitPrompt(payload.text),
    [submitPrompt],
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <Link
          to={`/story/p/${projectId}`}
          className="text-sm text-muted-foreground hover:text-foreground inline-block"
        >
          &larr; Back to project
        </Link>

        <ArtifactCard
          title="Story"
          prompt={userInputText || undefined}
          headerActions={
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-muted-foreground hover:text-foreground"
              aria-label="History"
              disabled={isGenerating}
              onClick={() => setIsHistoryOpen(true)}
            >
              <IconHistory className="size-3.5" />
            </Button>
          }
          content={
            <StoryContent
              storyText={storyText}
              isStreaming={isGenerating}
              error={error}
            />
          }
          isLoading={false}
          collapsible
          onRefine={handleStoryRefine}
          enableAttachments
        />

        <PlaceholderSection title="Characters" />
        <PlaceholderSection title="Scenes" />
      </div>

      <HistoryOverlay
        open={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        events={historyEvents ?? []}
      />
    </div>
  );
}

function PlaceholderSection({ title }: { title: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border/60 p-6">
      <p className="text-sm text-muted-foreground/50 text-center select-none">
        {title} — coming soon
      </p>
    </div>
  );
}

export default StoryWorkspace;
