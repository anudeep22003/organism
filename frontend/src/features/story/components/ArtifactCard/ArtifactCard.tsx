import { useEffect, useRef, useState } from "react";
import {
  IconPencil,
  IconAlertTriangle,
  IconChevronDown,
  IconChevronUp,
} from "@tabler/icons-react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import RefineInput from "./RefineInput";
import type { ArtifactCardProps } from "./types";

function ArtifactCard({
  title,
  content,
  isStale = false,
  isLoading = false,
  collapsible = false,
  onRefine,
  className,
}: ArtifactCardProps) {
  const [isRefineOpen, setIsRefineOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(!collapsible);
  const contentRef = useRef<HTMLDivElement>(null);
  const [hasOverflow, setHasOverflow] = useState(false);

  useEffect(() => {
    const node = contentRef.current;
    if (!node || !collapsible) return;
    const collapsedMax = window.innerHeight / 3;
    setHasOverflow(node.scrollHeight > collapsedMax);
  }, [content, collapsible]);

  const handleRefineSubmit = (text: string) => {
    onRefine?.(text);
    setIsRefineOpen(false);
  };

  const showExpandControl = collapsible && !isExpanded && hasOverflow;
  const showCollapseControl = collapsible && isExpanded && hasOverflow;

  return (
    <Card className={cn("gap-0 py-0 overflow-hidden", className)}>
      <CardHeader className="py-4 border-b border-border/40">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {isStale && (
          <Badge
            variant="outline"
            className="text-amber-500 border-amber-500/30 gap-1"
          >
            <IconAlertTriangle className="size-3" />
            Needs update
          </Badge>
        )}
      </CardHeader>

      <div className="relative">
        <CardContent
          ref={contentRef}
          className={cn(
            "py-4 min-h-[80px] transition-[max-height] duration-500 ease-in-out overflow-hidden",
            collapsible && !isExpanded && "max-h-[33vh]",
          )}
        >
          {isLoading ? <ArtifactSkeleton /> : content}
        </CardContent>

        {showExpandControl && (
          <div className="absolute inset-x-0 bottom-0 h-24 pointer-events-none bg-gradient-to-t from-card via-card/80 to-transparent" />
        )}
      </div>

      {isRefineOpen ? (
        <div className="w-full">
          <RefineInput
            onSubmit={handleRefineSubmit}
            onDismiss={() => setIsRefineOpen(false)}
            disabled={isLoading}
          />
        </div>
      ) : (
        (onRefine || hasOverflow) && (
          <CardFooter className="pb-3 pt-0 justify-between">
            {onRefine ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsRefineOpen(true)}
                className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                <IconPencil className="size-3.5" />
                Refine
              </Button>
            ) : (
              <div />
            )}
            {showExpandControl && (
              <button
                onClick={() => setIsExpanded(true)}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border border-border/60 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                <IconChevronDown className="size-3.5" />
                Expand
              </button>
            )}
            {showCollapseControl && (
              <button
                onClick={() => setIsExpanded(false)}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border border-border/60 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                <IconChevronUp className="size-3.5" />
                Collapse
              </button>
            )}
          </CardFooter>
        )
      )}
    </Card>
  );
}

function ArtifactSkeleton() {
  return (
    <div className="space-y-2.5 animate-pulse">
      <div className="h-3 bg-muted rounded w-3/4" />
      <div className="h-3 bg-muted rounded w-full" />
      <div className="h-3 bg-muted rounded w-5/6" />
      <div className="h-3 bg-muted rounded w-2/3" />
    </div>
  );
}

export default ArtifactCard;
