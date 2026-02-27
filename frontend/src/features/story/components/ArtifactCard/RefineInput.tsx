import { useCallback, useRef, useState } from "react";
import {
  IconMicrophone,
  IconPlayerStop,
  IconSend2,
  IconLoader2,
  IconX,
} from "@tabler/icons-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import WaveformIndicator from "@/components/InputBox/WaveformIndicator";
import { useVoiceRecorder } from "@/components/InputBox/useVoiceRecorder";

type RefineInputProps = {
  onSubmit: (text: string) => void;
  onDismiss: () => void;
  placeholder?: string;
  disabled?: boolean;
};

function RefineInput({
  onSubmit,
  onDismiss,
  placeholder = "Refine this artifact...",
  disabled = false,
}: RefineInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    el.style.overflowY = el.scrollHeight > 200 ? "auto" : "hidden";
  }, []);

  const handleTranscription = useCallback(
    (transcribed: string) => {
      setText((prev) => (prev ? `${prev}\n\n${transcribed}` : transcribed));
      requestAnimationFrame(adjustHeight);
    },
    [adjustHeight],
  );

  const { recordingState, visualizationData, toggleRecording } =
    useVoiceRecorder(handleTranscription);

  const handleSubmit = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText("");
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.overflowY = "hidden";
    }
  }, [text, disabled, onSubmit]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === "Escape") {
      onDismiss();
    }
  };

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";
  const canSubmit = text.trim().length > 0 && !disabled;

  return (
    <div className="border-t border-border/60">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          adjustHeight();
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isTranscribing}
        rows={1}
        className={cn(
          "w-full resize-none border-0 bg-transparent py-2.5 px-4 outline-none",
          "min-h-[40px] text-sm leading-relaxed",
          "placeholder:text-muted-foreground/60",
          "focus-visible:ring-0",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      />
      <div className="flex items-center gap-2 px-4 pb-3">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="icon"
              variant={isRecording ? "destructive" : "ghost"}
              onClick={toggleRecording}
              disabled={disabled || isTranscribing}
              className={cn(
                "size-7 rounded-md",
                isRecording && "animate-pulse",
              )}
              aria-label={isRecording ? "Stop recording" : "Record voice"}
            >
              {isTranscribing ? (
                <IconLoader2 className="size-3.5 animate-spin" />
              ) : isRecording ? (
                <IconPlayerStop className="size-3.5" />
              ) : (
                <IconMicrophone className="size-3.5" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {isTranscribing
              ? "Transcribing..."
              : isRecording
                ? "Stop recording"
                : "Record voice"}
          </TooltipContent>
        </Tooltip>

        {isRecording && visualizationData ? (
          <WaveformIndicator data={visualizationData} />
        ) : (
          <span className="text-muted-foreground/50 text-xs select-none">
            {navigator.platform.includes("Mac") ? "⌘" : "Ctrl"}+Enter
          </span>
        )}

        <div className="ml-auto flex items-center gap-1.5">
          <Button
            size="icon"
            variant="ghost"
            onClick={onDismiss}
            className="size-7 rounded-md text-muted-foreground"
            aria-label="Dismiss"
          >
            <IconX className="size-3.5" />
          </Button>
          <Button
            size="sm"
            variant="default"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="h-7 gap-1.5 text-xs"
            aria-label="Send refinement"
          >
            Refine
            <IconSend2 className="size-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default RefineInput;
