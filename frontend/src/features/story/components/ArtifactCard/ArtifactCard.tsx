import { useState } from "react";
import { IconPencil, IconAlertTriangle } from "@tabler/icons-react";
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
  onRefine,
  className,
}: ArtifactCardProps) {
  const [isRefineOpen, setIsRefineOpen] = useState(false);

  const handleRefineSubmit = (text: string) => {
    onRefine?.(text);
    setIsRefineOpen(false);
  };

  return (
    <Card className={cn("gap-0 py-0 overflow-hidden", className)}>
      <CardHeader className="py-4 border-b border-border/40">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {isStale && (
          <Badge variant="outline" className="text-amber-500 border-amber-500/30 gap-1">
            <IconAlertTriangle className="size-3" />
            Needs update
          </Badge>
        )}
      </CardHeader>

      <CardContent className="py-4 min-h-[80px]">
        {isLoading ? <ArtifactSkeleton /> : content}
      </CardContent>

      {onRefine && (
        isRefineOpen ? (
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
