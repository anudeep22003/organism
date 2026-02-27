import { useEffect, useState } from "react";
import { IconX } from "@tabler/icons-react";

type AttachmentPreviewProps = {
  files: File[];
  onRemove: (index: number) => void;
};

function AttachmentPreview({ files, onRemove }: AttachmentPreviewProps) {
  return (
    <div className="flex gap-2 px-4 pt-3 flex-wrap">
      {files.map((file, index) => (
        <Thumbnail key={`${file.name}-${index}`} file={file} onRemove={() => onRemove(index)} />
      ))}
    </div>
  );
}

function Thumbnail({ file, onRemove }: { file: File; onRemove: () => void }) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  return (
    <div className="relative group size-14 rounded-lg overflow-hidden border border-border/60 bg-muted shrink-0">
      {previewUrl && (
        <img
          src={previewUrl}
          alt={file.name}
          className="size-full object-cover"
        />
      )}
      <button
        onClick={onRemove}
        className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
      >
        <IconX className="size-3.5 text-white" />
      </button>
    </div>
  );
}

export default AttachmentPreview;
