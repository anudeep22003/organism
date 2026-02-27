import { useCallback, useRef, useState } from "react";
import {
  IconMicrophone,
  IconPlayerStop,
  IconSend2,
  IconLoader2,
  IconX,
  IconPhoto,
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
import type { RefinePayload } from "./types";
import AttachmentPreview from "./AttachmentPreview";

const ACCEPTED_IMAGE_TYPES = "image/png,image/jpeg,image/webp";

type RefineInputProps = {
  onSubmit: (payload: RefinePayload) => void;
  onDismiss: () => void;
  enableAttachments?: boolean;
  placeholder?: string;
  disabled?: boolean;
};

function RefineInput({
  onSubmit,
  onDismiss,
  enableAttachments = false,
  placeholder = "Refine this artifact...",
  disabled = false,
}: RefineInputProps) {
  const [text, setText] = useState("");
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleFilesSelected = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (files.length === 0) return;
      setStagedFiles((prev) => [...prev, ...files]);
      e.target.value = "";
    },
    [],
  );

  const removeFile = useCallback((index: number) => {
    setStagedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const resetState = useCallback(() => {
    setText("");
    setStagedFiles([]);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.overflowY = "hidden";
    }
  }, []);

  const canSubmit =
    (text.trim().length > 0 || stagedFiles.length > 0) && !disabled;

  const handleSubmit = useCallback(() => {
    if (!canSubmit) return;
    onSubmit({ text: text.trim(), attachments: stagedFiles });
    resetState();
  }, [canSubmit, text, stagedFiles, onSubmit, resetState]);

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

  return (
    <div className="border-t border-border/60">
      {stagedFiles.length > 0 && (
        <AttachmentPreview files={stagedFiles} onRemove={removeFile} />
      )}

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
        {enableAttachments && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_IMAGE_TYPES}
              multiple
              onChange={handleFilesSelected}
              className="hidden"
            />
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={disabled}
                  className="size-7 rounded-md"
                  aria-label="Add image"
                >
                  <IconPhoto className="size-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Add reference image</TooltipContent>
            </Tooltip>
          </>
        )}

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
