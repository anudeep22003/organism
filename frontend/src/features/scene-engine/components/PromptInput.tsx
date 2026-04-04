import { useCallback, useRef } from "react";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  Attachment01Icon,
  ArrowUp01Icon,
  Mic01Icon,
} from "@hugeicons/core-free-icons";
import { useVoiceRecorder } from "@/components/InputBox/useVoiceRecorder";
import { useAutoExpandTextarea } from "@/components/InputBox/useAutoExpandTextarea";
import WaveformIndicator from "./WaveformIndicator";

type PromptInputProps = {
  onSend: (value: string) => void;
  onUpload?: (files: File[]) => void;
  showUpload?: boolean;
  acceptedFileTypes?: string;
  placeholder?: string;
  maxHeightPx?: number;
  disabled?: boolean;
};

export default function PromptInput({
  onSend,
  onUpload,
  showUpload = true,
  acceptedFileTypes = "image/*",
  placeholder = "Input",
  maxHeightPx = 240,
  disabled = false,
}: PromptInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { textareaRef, adjustHeight, resetHeight } = useAutoExpandTextarea();

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
    useVoiceRecorder(handleTranscription);

  const handleSend = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    const trimmed = el.value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    el.value = "";
    resetHeight();
  }, [textareaRef, disabled, onSend, resetHeight]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length) onUpload?.(files);
    e.target.value = "";
  };

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";

  return (
    <div className="relative">
      {showUpload && (
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFileTypes}
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
      )}

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

      {/* Bottom-left: shortcut hint or waveform */}
      <div className="absolute bottom-2 left-3 flex items-center">
        {isRecording && visualizationData ? (
          <WaveformIndicator data={visualizationData} />
        ) : (
          <span className="select-none text-[10px] text-muted-foreground">
            {navigator.platform.includes("Mac") ? "⌘" : "Ctrl"}+↵
          </span>
        )}
      </div>

      {/* Bottom-right: action buttons */}
      <div className="absolute right-2 bottom-2 flex gap-1">
        {showUpload && (
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="flex items-center justify-center p-1.5 text-muted-foreground hover:bg-muted/40 disabled:opacity-50"
          >
            <HugeiconsIcon icon={Attachment01Icon} size={14} />
          </button>
        )}
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
        <button
          onClick={handleSend}
          disabled={disabled}
          className="flex items-center justify-center bg-foreground p-1.5 text-background hover:bg-foreground/80 disabled:opacity-50"
        >
          <HugeiconsIcon icon={ArrowUp01Icon} size={14} />
        </button>
      </div>
    </div>
  );
}
