import { IconFeather } from "@tabler/icons-react";
import { ScrollArea } from "@/components/ui/scroll-area";

type ArtifactPanelProps = {
  storyText: string;
  isStreaming: boolean;
};

function ArtifactPlaceholder() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 select-none">
      <IconFeather className="size-10 text-muted-foreground/40" strokeWidth={1} />
      <div className="text-center space-y-1">
        <p className="text-sm text-muted-foreground">
          Your story will appear here
        </p>
        <p className="text-xs text-muted-foreground/60">
          Enter a prompt to begin
        </p>
      </div>
    </div>
  );
}

function ArtifactPanel({ storyText, isStreaming }: ArtifactPanelProps) {
  if (!storyText) {
    return <ArtifactPlaceholder />;
  }

  return (
    <ScrollArea className="h-full">
      <div className="max-w-[65ch] mx-auto px-8 py-10">
        <article className="prose prose-stone dark:prose-invert prose-sm leading-[1.8] text-foreground/90">
          <div className="whitespace-pre-wrap font-serif text-[15px]">
            {storyText}
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1.1em] bg-foreground/60 ml-0.5 align-text-bottom animate-pulse" />
            )}
          </div>
        </article>
      </div>
    </ScrollArea>
  );
}

export default ArtifactPanel;
