import { IconFeather } from "@tabler/icons-react";

type StoryContentProps = {
  storyText: string;
  isStreaming: boolean;
};

function StoryContent({ storyText, isStreaming }: StoryContentProps) {
  if (!storyText && !isStreaming) {
    return <StoryPlaceholder />;
  }

  return (
    <article className="prose prose-stone dark:prose-invert prose-sm leading-[1.8] text-foreground/90">
      <div className="whitespace-pre-wrap font-serif text-[15px]">
        {storyText}
        {isStreaming && (
          <span className="inline-block w-0.5 h-[1.1em] bg-foreground/60 ml-0.5 align-text-bottom animate-pulse" />
        )}
      </div>
    </article>
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
