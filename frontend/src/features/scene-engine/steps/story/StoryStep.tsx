import Block from "../../components/Block";
import PromptInput from "../../components/PromptInput";
import { useSceneEngine } from "../../context";
import { useStoryPhase } from "./hooks/useStoryPhase";

function StoryCanvas({
  storyText,
  isGenerating,
  error,
}: {
  storyText: string;
  isGenerating: boolean;
  error?: string;
}) {
  if (error && !storyText) {
    return (
      <div className="flex h-full w-full items-center justify-center border border-border bg-muted/20 p-4">
        <span className="text-xs text-destructive">{error}</span>
      </div>
    );
  }

  if (!storyText && !isGenerating) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-2 border border-border bg-muted/20 select-none">
        <span className="text-xs text-muted-foreground">
          Your story will appear here
        </span>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col border border-border bg-muted/20">
      <div className="flex-1 overflow-y-auto p-4">
        <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
          {storyText}
          {isGenerating && (
            <span className="ml-0.5 inline-block h-[1em] w-0.5 animate-pulse bg-foreground/60 align-text-bottom" />
          )}
        </p>
        {error && storyText && (
          <p className="mt-3 text-xs text-destructive">
            Generation interrupted. Submit a new prompt to continue.
          </p>
        )}
      </div>
    </div>
  );
}

function ChatPanel({ onSend }: { onSend: (value: string) => void }) {
  return (
    <div className="flex h-full w-full flex-col border border-border">
      <div className="flex-1" />
      <PromptInput onSend={onSend} showUpload={false} placeholder="Write your story prompt..." />
    </div>
  );
}

export default function StoryStep() {
  const { projectId, storyId } = useSceneEngine();
  const { storyText, isGenerating, error, submitPrompt } = useStoryPhase(
    projectId,
    storyId,
  );

  return (
    <div className="flex h-full w-full p-4">
      <Block
        tabs={[
          { id: "story", label: "Story", panel: "left" },
          { id: "chat", label: "Chat", panel: "right" },
        ]}
        leftContent={
          <StoryCanvas
            storyText={storyText}
            isGenerating={isGenerating}
            error={error}
          />
        }
        rightContent={<ChatPanel onSend={submitPrompt} />}
      />
    </div>
  );
}
