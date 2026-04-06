import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { imageSignedUrlOptions } from "@scene-engine/shared/scene-engine.queries";
import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";

type ReferenceImageViewerProps = {
  img: ImageRecord;
  onBack: () => void;
  onDelete: () => void;
  isDeleting: boolean;
};

export function ReferenceImageViewer({
  img,
  onBack,
  onDelete,
  isDeleting,
}: ReferenceImageViewerProps) {
  const { data } = useQuery(imageSignedUrlOptions(img.id));

  return (
    <div className="absolute inset-0 z-30 flex flex-col border border-border bg-background">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-3 py-2">
        <span className="text-[10px] text-muted-foreground">{img.id}</span>
        <div className="flex gap-2">
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="border border-border px-2 py-1 text-[10px] text-muted-foreground hover:bg-muted/40 disabled:opacity-50"
          >
            {isDeleting ? "Deleting…" : "Delete"}
          </button>
          <button
            onClick={onBack}
            className="bg-foreground px-2 py-1 text-[10px] text-background hover:bg-foreground/80"
          >
            ← Back
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 items-center justify-center bg-muted/10 p-4">
        {data?.url ? (
          <img
            src={data.url}
            alt=""
            className="max-h-full max-w-full object-contain"
          />
        ) : (
          <Skeleton className="h-full w-full" />
        )}
      </div>
    </div>
  );
}
