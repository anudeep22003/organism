import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE } from "./scene-engine.constants";

export const imageSignedUrlOptions = (imageId: string) =>
  queryOptions({
    queryKey: ["image", imageId, "signed-url"] as const,
    queryFn: () =>
      httpClient.get<{ url: string; expiresAt: string }>(
        `${STORY_API_BASE}/image/${imageId}/signed-url`,
      ),
    enabled: !!imageId,
    staleTime: 55 * 60 * 1000,
  });
