import type { Actor } from "@/socket/envelopeType";
import { Loader2 } from "lucide-react";

interface TabLabelProps {
  actor: Actor;
  isStreaming: boolean;
}

export const TabLabel = ({ actor, isStreaming }: TabLabelProps) => {
  if (actor === "assistant") {
    return null;
  }
  return (
    <div className="flex items-center gap-2">
      {actor}
      {isStreaming && <Loader2 className="h-3 w-3 animate-spin" />}
    </div>
  );
};
