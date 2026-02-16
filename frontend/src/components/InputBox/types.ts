export type InputBoxProps = {
  onSubmit: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
  submitLabel?: string;
};

export type RecordingState = "idle" | "recording" | "transcribing";
