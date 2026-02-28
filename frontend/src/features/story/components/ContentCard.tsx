import { useEffect, useRef, useState, type ReactNode } from "react";
import { IconChevronDown } from "@tabler/icons-react";
import { cn } from "@/lib/utils";

type ContentCardProps = {
  prompt?: string;
  children: ReactNode;
  collapsible?: boolean;
  maxCollapsedHeight?: string;
  expanded?: boolean;
  onToggleExpand?: () => void;
  className?: string;
};

function ContentCard({
  prompt,
  children,
  collapsible = false,
  maxCollapsedHeight = "33vh",
  expanded,
  onToggleExpand,
  className,
}: ContentCardProps) {
  const [internalExpanded, setInternalExpanded] = useState(!collapsible);
  const contentRef = useRef<HTMLDivElement>(null);
  const [hasOverflow, setHasOverflow] = useState(false);

  const isExpanded = expanded ?? internalExpanded;
  const toggleExpand = onToggleExpand ?? (() => setInternalExpanded((v) => !v));

  useEffect(() => {
    const node = contentRef.current;
    if (!node || !collapsible) return;
    const maxPx =
      maxCollapsedHeight === "33vh"
        ? window.innerHeight / 3
        : parseInt(maxCollapsedHeight);
    setHasOverflow(node.scrollHeight > maxPx);
  }, [children, collapsible, maxCollapsedHeight]);

  const isCollapsed = collapsible && !isExpanded && hasOverflow;

  return (
    <div className={cn("relative", className)}>
      {prompt && <PromptBlock text={prompt} />}
      <div
        ref={contentRef}
        className={cn(
          "px-6 py-4 min-h-[80px] transition-[max-height] duration-500 ease-in-out overflow-hidden",
          isCollapsed && `max-h-[${maxCollapsedHeight}]`,
        )}
      >
        {children}
      </div>
      {isCollapsed && (
        <button
          onClick={toggleExpand}
          className="absolute inset-x-0 bottom-0 h-24 flex items-end justify-center pb-2 bg-linear-to-t from-card via-card/80 to-transparent cursor-pointer group transition-all"
        >
          <IconChevronDown className="size-4 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors" />
        </button>
      )}
    </div>
  );
}

function PromptBlock({ text }: { text: string }) {
  return (
    <div className="px-6 pt-4 pb-2">
      <div className="rounded-lg bg-muted/50 px-3 py-2.5 border-l-2 border-muted-foreground/20">
        <p className="text-xs text-muted-foreground/70 whitespace-pre-wrap leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  );
}

export default ContentCard;
