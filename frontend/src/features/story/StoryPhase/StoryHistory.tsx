import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { IconCheck, IconHistory, IconX } from "@tabler/icons-react";
import type { EditEventType } from "./types";

function formatRelativeTime(dateString: string): string {
  const now = Date.now();
  const then = new Date(dateString).getTime();
  const diffSeconds = Math.floor((now - then) / 1000);

  if (diffSeconds < 60) return "just now";
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
  if (diffSeconds < 86400)
    return `${Math.floor(diffSeconds / 3600)}h ago`;
  return `${Math.floor(diffSeconds / 86400)}d ago`;
}

function formatOperationType(operationType: string): string {
  return operationType === "generate_story" ? "Generated" : "Refined";
}

function StatusIcon({ status }: { status: string }) {
  if (status === "succeeded") {
    return <IconCheck className="size-3 text-emerald-500" />;
  }
  if (status === "failed") {
    return <IconX className="size-3 text-red-500" />;
  }
  return (
    <div className="size-3 rounded-full bg-muted-foreground/30 animate-pulse" />
  );
}

function StoryHistory({ events }: { events: EditEventType[] }) {
  if (events.length === 0) {
    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-muted-foreground/50"
            aria-label="History"
          >
            <IconHistory className="size-3.5" />
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-64 p-3">
          <p className="text-xs text-muted-foreground text-center">
            No history yet
          </p>
        </PopoverContent>
      </Popover>
    );
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-7 text-muted-foreground hover:text-foreground"
          aria-label="History"
        >
          <IconHistory className="size-3.5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-auto max-w-[90vw] p-0">
        <div className="px-3 py-2 border-b border-border/40">
          <p className="text-xs font-medium text-muted-foreground">
            History
          </p>
        </div>
        <div className="flex overflow-x-auto gap-2 p-3">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

function EventCard({ event }: { event: EditEventType }) {
  return (
    <div
      className={cn(
        "shrink-0 w-48 rounded-lg border border-border/60 p-2.5",
        "bg-muted/30 hover:bg-muted/50 transition-colors",
      )}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] text-muted-foreground">
          {formatRelativeTime(event.createdAt)}
        </span>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-muted-foreground">
            {formatOperationType(event.operationType)}
          </span>
          <StatusIcon status={event.status} />
        </div>
      </div>
      <p className="text-xs text-foreground/80 line-clamp-2 leading-relaxed">
        {event.userInstruction}
      </p>
    </div>
  );
}

export default StoryHistory;
