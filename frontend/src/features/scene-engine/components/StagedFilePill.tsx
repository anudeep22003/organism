import { File01Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useEffect, useState } from "react";

type StagedFilePillProps = {
  file: File;
  disabled: boolean;
  onRemove: () => void;
};

export function StagedFilePill({ file, disabled, onRemove }: StagedFilePillProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <span className="flex items-center gap-1 border border-border px-1.5 py-0.5">
      {previewUrl ? (
        <img src={previewUrl} alt={file.name} className="h-4 w-4 shrink-0 object-cover" />
      ) : (
        <HugeiconsIcon icon={File01Icon} size={12} className="shrink-0 text-muted-foreground" />
      )}
      <span className="text-[10px] text-muted-foreground">{file.name}</span>
      <button
        onClick={onRemove}
        disabled={disabled}
        className="text-[10px] text-muted-foreground hover:text-foreground disabled:opacity-50"
      >
        ✕
      </button>
    </span>
  );
}
