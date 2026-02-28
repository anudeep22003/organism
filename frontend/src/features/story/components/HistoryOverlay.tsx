import { useCallback, useEffect } from "react";
import { IconX } from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import type { EditEventType } from "../StoryPhase/types";
import HistoryCard from "./HistoryCard";

type HistoryOverlayProps = {
  open: boolean;
  onClose: () => void;
  events: EditEventType[];
};

function HistoryOverlay({ open, onClose, events }: HistoryOverlayProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative z-10 flex items-center justify-between px-6 pt-5 pb-3">
        <h2 className="text-sm font-medium text-white/80">History</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="size-8 text-white/60 hover:text-white hover:bg-white/10"
          aria-label="Close history"
        >
          <IconX className="size-4" />
        </Button>
      </div>

      <div className="relative z-10 flex-1 min-h-0 flex items-stretch py-4">
        {events.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-white/40">No history yet</p>
          </div>
        ) : (
          <div
            className="flex gap-4 overflow-x-auto snap-x snap-mandatory w-full px-[10vw] items-stretch"
            style={{ scrollPaddingInline: "10vw" }}
          >
            {events.map((event) => (
              <HistoryCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default HistoryOverlay;
