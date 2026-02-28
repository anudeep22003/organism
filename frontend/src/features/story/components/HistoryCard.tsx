import { IconCheck, IconX } from "@tabler/icons-react";
import { Card, CardHeader } from "@/components/ui/card";
import type { EditEventType } from "../StoryPhase/types";
import ContentCard from "./ContentCard";

function formatRelativeTime(dateString: string): string {
  const diffSeconds = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (diffSeconds < 60) return "just now";
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
  return `${Math.floor(diffSeconds / 86400)}d ago`;
}

function formatOperationType(operationType: string): string {
  return operationType === "generate_story" ? "Generated" : "Refined";
}

function StatusIcon({ status }: { status: string }) {
  if (status === "succeeded") return <IconCheck className="size-3 text-emerald-500" />;
  if (status === "failed") return <IconX className="size-3 text-red-500" />;
  return <div className="size-3 rounded-full bg-muted-foreground/30 animate-pulse" />;
}

function HistoryCard({ event }: { event: EditEventType }) {
  const storyText = event.outputSnapshot?.storyText ?? "";

  return (
    <Card className="gap-0 py-0 overflow-hidden bg-card/80 border-border/40 w-96 flex-shrink-0 snap-center">
      <CardHeader className="py-3 px-4 border-b border-border/30 flex flex-row items-center justify-between">
        <span className="text-[11px] text-muted-foreground/60">
          {formatRelativeTime(event.createdAt)}
        </span>
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-muted-foreground/60">
            {formatOperationType(event.operationType)}
          </span>
          <StatusIcon status={event.status} />
        </div>
      </CardHeader>
      <ContentCard
        prompt={event.userInstruction}
        collapsible
        maxCollapsedHeight="300px"
      >
        {storyText ? (
          <article className="prose prose-stone dark:prose-invert prose-sm leading-[1.8] text-foreground/70">
            <div className="whitespace-pre-wrap font-serif text-[14px]">
              {storyText}
            </div>
          </article>
        ) : (
          <p className="text-xs text-muted-foreground/40 italic">
            No output recorded
          </p>
        )}
      </ContentCard>
    </Card>
  );
}

export default HistoryCard;
