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

  const cardRef = useRef<HTMLDivElement>(null);
  const [isCardVisible, setIsCardVisible] = useState(false);

  const isCollapsed = collapsible && !isExpanded && hasOverflow;
  const showFloatingCollapse = collapsible && isExpanded && hasOverflow && isCardVisible;

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

  return (
    <Card ref={cardRef} className={cn("gap-0 py-0 overflow-hidden", className)}>
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
            isCollapsed && "max-h-[33vh]",
          )}
        >
          {isLoading ? <ArtifactSkeleton /> : content}
        </CardContent>

        {isCollapsed && (
          <button
            onClick={() => setIsExpanded(true)}
            className="absolute inset-x-0 bottom-0 h-24 flex items-end justify-center pb-2 bg-gradient-to-t from-card via-card/80 to-transparent cursor-pointer group transition-all"
          >
            <IconChevronDown className="size-4 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors" />
          </button>
        )}
      </div>

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
