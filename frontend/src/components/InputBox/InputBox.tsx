import { useCallback, useState } from "react";
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
  InputGroupTextarea,
} from "@/components/ui/input-group";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import WaveformIndicator from "./WaveformIndicator";
import { useVoiceRecorder } from "./useVoiceRecorder";
import { useAutoExpandTextarea } from "./useAutoExpandTextarea";
import type { InputBoxProps } from "./types";

function InputBox({
  onSubmit,
  placeholder = "Describe your vision...",
  disabled = false,
  submitLabel = "Send",
}: InputBoxProps) {
  const [text, setText] = useState("");
  const { textareaRef, adjustHeight, resetHeight } =
    useAutoExpandTextarea();

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
    resetHeight();
  }, [text, disabled, onSubmit, resetHeight]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextChange = (
    e: React.ChangeEvent<HTMLTextAreaElement>,
  ) => {
    setText(e.target.value);
    adjustHeight();
  };

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";
  const canSubmit = text.trim().length > 0 && !disabled;

  return (
    <InputGroup className="border-border bg-background">
      <InputGroupTextarea
        ref={textareaRef}
        value={text}
        onChange={handleTextChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isTranscribing}
        className="min-h-[60px] max-h-[80vh] text-sm leading-relaxed"
        rows={2}
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
