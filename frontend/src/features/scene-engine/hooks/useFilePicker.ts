import { useRef } from "react";

const DEFAULT_MAX_FILE_SIZE_MB = 5;

type UseFilePickerOptions = {
  accept: string;
  multiple?: boolean;
  maxFileSizeMb?: number;
  onPick: (files: File[]) => void;
  onReject: (reason: string) => void;
};

function fileMatchesAccept(file: File, accept: string): boolean {
  return accept.split(",").map((s) => s.trim()).some((token) => {
    if (token.endsWith("/*")) {
      return file.type.startsWith(token.slice(0, -1));
    }
    if (token.startsWith(".")) {
      return file.name.toLowerCase().endsWith(token.toLowerCase());
    }
    return file.type === token;
  });
}

export function useFilePicker({
  accept,
  multiple = false,
  maxFileSizeMb = DEFAULT_MAX_FILE_SIZE_MB,
  onPick,
  onReject,
}: UseFilePickerOptions) {
  const inputRef = useRef<HTMLInputElement>(null);

  const triggerPick = () => inputRef.current?.click();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (!picked.length) return;

    const maxBytes = maxFileSizeMb * 1024 * 1024;
    const valid: File[] = [];
    const rejectionReasons: string[] = [];

    for (const file of picked) {
      if (!fileMatchesAccept(file, accept)) {
        rejectionReasons.push(`${file.name} is not an accepted file type`);
      } else if (file.size > maxBytes) {
        rejectionReasons.push(`${file.name} exceeds the ${maxFileSizeMb} MB limit`);
      } else {
        valid.push(file);
      }
    }

    if (valid.length) onPick(valid);

    if (rejectionReasons.length) {
      const prefix = rejectionReasons.length > 1
        ? `${rejectionReasons.length} files rejected: `
        : "";
      onReject(prefix + rejectionReasons.join(", "));
    }
  };

  const inputProps = {
    ref: inputRef,
    type: "file" as const,
    accept,
    multiple,
    className: "hidden",
    onChange: handleChange,
  };

  return { triggerPick, inputProps };
}
