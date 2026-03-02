import { useEffect, useRef, useState } from "react";
import {
  IconPencil,
  IconAlertTriangle,
  IconChevronUp,
} from "@tabler/icons-react";
import {
  Card,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import ContentCard from "../ContentCard";
import RefineInput from "./RefineInput";
import type { ArtifactCardProps, RefinePayload } from "./types";

function ArtifactCard({
  title,
  prompt,
  content,
  headerActions,
  isStale = false,
  isLoading = false,
  collapsible = false,
  enableAttachments = false,
  onRefine,
  className,
}: ArtifactCardProps) {
  const [isRefineOpen, setIsRefineOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(!collapsible);
  const cardRef = useRef<HTMLDivElement>(null);
  const [isCardVisible, setIsCardVisible] = useState(false);

  useEffect(() => {
    const card = cardRef.current;
    if (!card || !collapsible) return;
    const observer = new IntersectionObserver(
      ([entry]) => setIsCardVisible(entry.isIntersecting),
      { threshold: 0.1 },
    );
    observer.observe(card);
    return () => observer.disconnect();
  }, [collapsible]);

  const handleRefineSubmit = (payload: RefinePayload) => {
    onRefine?.(payload);
    setIsRefineOpen(false);
  };

  const showFloatingCollapse = collapsible && isExpanded && isCardVisible;

  return (
    <Card ref={cardRef} className={cn("gap-0 py-0 overflow-hidden", className)}>
      <CardHeader className="py-4 border-b border-border/40 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {isStale && (
            <Badge
              variant="outline"
              className="text-warning border-warning/30 gap-1"
            >
              <IconAlertTriangle className="size-3" />
              Needs update
            </Badge>
          )}
        </div>
        {headerActions && <div className="flex items-center gap-1">{headerActions}</div>}
      </CardHeader>

      {isLoading ? (
        <div className="px-6 py-4 min-h-[80px]">
          <ArtifactSkeleton />
        </div>
      ) : (
        <ContentCard
          prompt={prompt}
          collapsible={collapsible}
          expanded={isExpanded}
          onToggleExpand={() => setIsExpanded((v) => !v)}
        >
          {content}
        </ContentCard>
      )}

      {showFloatingCollapse && (
        <button
          onClick={() => setIsExpanded(false)}
          className="fixed bottom-6 right-6 z-50 p-2.5 rounded-full bg-card border border-border/60 text-muted-foreground/60 hover:text-foreground hover:border-border shadow-lg backdrop-blur-sm transition-all cursor-pointer"
        >
          <IconChevronUp className="size-4" />
        </button>
      )}

      {onRefine &&
        (isRefineOpen ? (
          <div className="w-full">
            <RefineInput
              onSubmit={handleRefineSubmit}
              onDismiss={() => setIsRefineOpen(false)}
              enableAttachments={enableAttachments}
              disabled={isLoading}
            />
          </div>
        ) : (
          <CardFooter className="pb-3 pt-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsRefineOpen(true)}
              className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            >
              <IconPencil className="size-3.5" />
              Refine
            </Button>
          </CardFooter>
        ))}
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
