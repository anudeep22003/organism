import { useVoiceRecorder } from "@/components/InputBox/useVoiceRecorder";
import { Mic01Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useCallback, useEffect } from "react";

type VoiceTextareaProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
  maxRecordingMs?: number;
};

export default function VoiceTextarea({
  value,
  onChange,
  placeholder,
  rows = 3,
  disabled = false,
  maxRecordingMs = 60_000,
}: VoiceTextareaProps) {
  const handleTranscription = useCallback(
    (transcribed: string) => {
      onChange(value ? `${value}\n\n${transcribed}` : transcribed);
    },
    [value, onChange],
  );

  const { recordingState, toggleRecording } =
    useVoiceRecorder(handleTranscription);

  const isRecording = recordingState === "recording";
  const isTranscribing = recordingState === "transcribing";

  useEffect(() => {
    if (!isRecording) return;
    const timer = setTimeout(() => void toggleRecording(), maxRecordingMs);
    return () => clearTimeout(timer);
  }, [isRecording, toggleRecording, maxRecordingMs]);

  return (
    <div className="relative">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        disabled={disabled || isTranscribing}
        className="w-full resize-none border border-border bg-background px-3 py-2 pr-10 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50"
      />
      <button
        type="button"
        onClick={() => void toggleRecording()}
        disabled={disabled || isTranscribing}
        className={`absolute bottom-2 right-2 flex items-center justify-center p-1 disabled:opacity-50 ${
          isRecording
            ? "animate-pulse text-destructive"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <HugeiconsIcon icon={Mic01Icon} size={14} />
      </button>
    </div>
  );
}
