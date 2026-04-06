import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "@scene-engine/components/Skeleton";
import { imageSignedUrlOptions } from "../../character.queries";
import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";

function RefImageThumbnail({
  img,
  isLast,
  onClick,
}: {
  img: ImageRecord;
  isLast: boolean;
  onClick?: () => void;
}) {
  const queryClient = useQueryClient();
  const { data } = useQuery(imageSignedUrlOptions(img.id));

  return (
    <div
      onClick={onClick}
      className={`relative aspect-square w-full shrink-0 cursor-pointer bg-muted/20 hover:bg-muted/40 ${
        !isLast ? "border-b border-border" : ""
      }`}
    >
      {data?.url ? (
        <img
          src={data.url}
          alt=""
          className="h-full w-full object-cover"
          onError={() =>
            void queryClient.invalidateQueries({
              queryKey: imageSignedUrlOptions(img.id).queryKey,
            })
          }
        />
      ) : (
        <Skeleton className="h-full w-full" />
      )}
    </div>
  );
}

type RefImageTrayProps = {
  images: ImageRecord[];
  variant: "card" | "modal";
  onImageClick?: (imageId: string) => void;
};

export function RefImageTray({ images, variant, onImageClick }: RefImageTrayProps) {
  const outerClass =
    variant === "card"
      ? `border border-l-0 ${images.length > 0 ? "border-border" : "border-transparent"}`
      : "";

  return (
    <div className={`flex w-16 shrink-0 self-end flex-col overflow-y-auto ${outerClass}`}>
      {images.map((img, i) => (
        <RefImageThumbnail
          key={img.id}
          img={img}
          isLast={i === images.length - 1}
          onClick={onImageClick ? () => onImageClick(img.id) : undefined}
        />
      ))}
    </div>
  );
}
