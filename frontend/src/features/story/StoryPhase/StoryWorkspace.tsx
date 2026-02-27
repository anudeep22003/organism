import { Link, useParams } from "react-router";
import { ArtifactCard } from "../components/ArtifactCard";
import StoryContent from "../components/StoryContent";
import { useStoryPhase } from "./hooks/useStoryPhase";

function StoryWorkspace() {
  const { projectId, storyId } = useParams();
  const { storyText, isGenerating, submitPrompt } = useStoryPhase(
    projectId ?? "",
    storyId ?? "",
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
          content={
            <StoryContent storyText={storyText} isStreaming={isGenerating} />
          }
          isLoading={false}
          onRefine={submitPrompt}
        />

        <PlaceholderSection title="Characters" />
        <PlaceholderSection title="Scenes" />
      </div>
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
