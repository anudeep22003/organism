import { useAutoExpandTextarea } from "@/components/InputBox/useAutoExpandTextarea";
import { useVoiceRecorder } from "@/components/InputBox/useVoiceRecorder";
import {
  ArrowUp01Icon,
  Attachment01Icon,
  Mic01Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useCallback, useState } from "react";
import { useFilePicker } from "../hooks/useFilePicker";
import { StagedFilePill } from "./StagedFilePill";
import { ValidationErrorBlock } from "./ValidationErrorBlock";
import WaveformIndicator from "./WaveformIndicator";

type PromptInputProps = {
  onSend: (value: string, files: File[]) => void;
  placeholder?: string;
  maxHeightPx?: number;
  disabled?: boolean;
  enableUploads?: boolean;
  acceptedFileTypes?: string;
  maxFiles?: number;
  maxFileSizeMb?: number;
  enableVoiceTranscription?: boolean;
};

export default function PromptInput({
  onSend,
  placeholder = "Input",
  maxHeightPx = 240,
  disabled = false,
  enableUploads = false,
  acceptedFileTypes = "image/*",
  maxFiles = 3,
  maxFileSizeMb = 5,
  enableVoiceTranscription = false,
}: PromptInputProps) {
  const { textareaRef, adjustHeight, resetHeight } = useAutoExpandTextarea();
  const [stagedFiles, setStagedFiles] = useState<File[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);

  const { triggerPick, inputProps } = useFilePicker({
    accept: acceptedFileTypes,
    multiple: maxFiles !== 1,
    maxFileSizeMb,
    onPick: (files) =>
      setStagedFiles((prev) => {
        const combined = [...prev, ...files];
        return maxFiles === Infinity ? combined : combined.slice(0, maxFiles);
      }),
    onReject: setValidationError,
  });

  const handleTranscription = useCallback(
    (transcribed: string) => {
      const el = textareaRef.current;
      if (!el) return;
      el.value = el.value ? `${el.value}\n\n${transcribed}` : transcribed;
      requestAnimationFrame(adjustHeight);
    },
    [textareaRef, adjustHeight],
  );

  const { recordingState, visualizationData, toggleRecording } =
    useVoiceRecorder(enableVoiceTranscription ? handleTranscription : () => {});

  const handleSend = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    const trimmed = el.value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed, stagedFiles);
    el.value = "";
    resetHeight();
    setStagedFiles([]);
  }, [textareaRef, disabled, onSend, stagedFiles, resetHeight]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const removeFile = (index: number) =>
    setStagedFiles((prev) => prev.filter((_, i) => i !== index));

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";
  const uploadsAtMax = stagedFiles.length >= maxFiles;

  return (
    <div className="flex flex-col">
      {enableUploads && <input {...inputProps} />}

      {stagedFiles.length > 0 && (
        <div className="shrink-0 border-b border-border px-3 py-1.5">
          <div className="flex flex-wrap gap-2">
            {stagedFiles.map((file, i) => (
              <StagedFilePill
                key={i}
                file={file}
                disabled={disabled}
                onRemove={() => removeFile(i)}
              />
            ))}
          </div>
        </div>
      )}

      {validationError && (
        <ValidationErrorBlock
          message={validationError}
          onClear={() => setValidationError(null)}
        />
      )}

      <div className="relative">
        <textarea
          ref={textareaRef}
          placeholder={placeholder}
          disabled={disabled || isTranscribing}
          rows={3}
          onKeyDown={handleKeyDown}
          onChange={adjustHeight}
          style={{ maxHeight: maxHeightPx }}
          className="w-full resize-none bg-transparent px-3 py-2 pr-20 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50"
        />

        <div className="absolute bottom-2 left-3 flex items-center">
          {isRecording && visualizationData ? (
            <WaveformIndicator data={visualizationData} />
          ) : (
            <span className="select-none text-[10px] text-muted-foreground">
              {navigator.platform.includes("Mac") ? "⌘" : "Ctrl"}+↵
            </span>
          )}
        </div>

        <div className="absolute right-2 bottom-2 flex gap-1">
          {enableUploads && (
            <button
              onClick={triggerPick}
              disabled={disabled || uploadsAtMax}
              className="flex items-center justify-center p-1.5 text-muted-foreground hover:bg-muted/40 disabled:opacity-50"
            >
              <HugeiconsIcon icon={Attachment01Icon} size={14} />
            </button>
          )}
          {enableVoiceTranscription && (
            <button
              onClick={() => { void toggleRecording(); }}
              disabled={disabled || isTranscribing}
              className={`flex items-center justify-center p-1.5 disabled:opacity-50 ${
                isRecording
                  ? "animate-pulse text-destructive hover:bg-muted/40"
                  : "text-muted-foreground hover:bg-muted/40"
              }`}
            >
              <HugeiconsIcon icon={Mic01Icon} size={14} />
            </button>
          )}
          <button
            onClick={handleSend}
            disabled={disabled}
            className="flex items-center justify-center bg-foreground p-1.5 text-background hover:bg-foreground/80 disabled:opacity-50"
          >
            <HugeiconsIcon icon={ArrowUp01Icon} size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
