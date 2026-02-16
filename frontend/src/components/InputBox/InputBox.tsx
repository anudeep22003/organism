import { useCallback, useRef, useState } from "react";
import {
  IconMicrophone,
  IconPlayerStop,
  IconSend2,
  IconLoader2,
} from "@tabler/icons-react";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
} from "@/components/ui/input-group";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import WaveformIndicator from "./WaveformIndicator";
import { useVoiceRecorder } from "./useVoiceRecorder";
import type { InputBoxProps } from "./types";

function InputBox({
  onSubmit,
  placeholder = "Describe your vision...",
  disabled = false,
  submitLabel = "Send",
}: InputBoxProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "0";
    const maxHeight = window.innerHeight * 0.8;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
    el.style.overflowY = el.scrollHeight > maxHeight ? "auto" : "hidden";
  }, []);

  const handleTranscription = useCallback(
    (transcribed: string) => {
      setText((prev) =>
        prev ? `${prev}\n\n${transcribed}` : transcribed,
      );
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
  };

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";
  const canSubmit = text.trim().length > 0 && !disabled;

  return (
    <InputGroup className="border-border bg-background">
      <textarea
        ref={textareaRef}
        data-slot="input-group-control"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          adjustHeight();
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isTranscribing}
        rows={2}
        className={cn(
          "w-full resize-none rounded-none border-0 bg-transparent py-3 px-3 shadow-none outline-none",
          "min-h-[60px] text-sm leading-relaxed",
          "placeholder:text-muted-foreground",
          "focus-visible:ring-0",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      />
      <InputGroupAddon align="block-end" className="border-t border-border/60">
        <Tooltip>
          <TooltipTrigger asChild>
            <InputGroupButton
              size="icon-xs"
              variant={isRecording ? "destructive" : "ghost"}
              onClick={toggleRecording}
              disabled={disabled || isTranscribing}
              className={
                isRecording
                  ? "animate-pulse"
                  : ""
              }
              aria-label={isRecording ? "Stop recording" : "Record voice"}
            >
              {isTranscribing ? (
                <IconLoader2 className="animate-spin" />
              ) : isRecording ? (
                <IconPlayerStop />
              ) : (
                <IconMicrophone />
              )}
            </InputGroupButton>
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
          <span className="text-muted-foreground text-xs select-none">
            {navigator.platform.includes("Mac") ? "⌘" : "Ctrl"}+↵
          </span>
        )}

        <InputGroupButton
          size="sm"
          variant="default"
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="ml-auto"
          aria-label={submitLabel}
        >
          {submitLabel}
          <IconSend2 className="size-3.5" />
        </InputGroupButton>
      </InputGroupAddon>
    </InputGroup>
  );
}

export default InputBox;
