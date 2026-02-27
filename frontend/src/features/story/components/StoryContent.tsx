import { IconFeather, IconAlertCircle } from "@tabler/icons-react";

type StoryContentProps = {
  storyText: string;
  isStreaming: boolean;
  error?: string;
};

function StoryContent({ storyText, isStreaming, error }: StoryContentProps) {
  if (!storyText && !isStreaming && !error) {
    return <StoryPlaceholder />;
  }

  return (
    <div className="space-y-4">
      {storyText && (
        <article className="prose prose-stone dark:prose-invert prose-sm leading-[1.8] text-foreground/90">
          <div className="whitespace-pre-wrap font-serif text-[15px]">
            {storyText}
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1.1em] bg-foreground/60 ml-0.5 align-text-bottom animate-pulse" />
            )}
          </div>
        </article>
      )}
      {error && (
        <div className="flex items-start gap-2 text-sm text-destructive/80">
          <IconAlertCircle className="size-4 mt-0.5 shrink-0" />
          <p>
            {storyText
              ? "Generation was interrupted. Use Refine to try again."
              : error}
          </p>
        </div>
      )}
    </div>
  );
}

function StoryPlaceholder() {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3 select-none">
      <IconFeather
        className="size-8 text-muted-foreground/30"
        strokeWidth={1}
      />
      <p className="text-sm text-muted-foreground/60">
        Your story will appear here
      </p>
    </div>
  );
}

export default StoryContent;
