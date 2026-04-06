import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import type { CharacterBundle } from "./character-extraction.types";

const STORY_API_BASE = "/api/comic-builder/v2" as const;
const STORY_QUERY_ROOT = ["story"] as const;

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

export const charactersOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project",
      projectId,
      "story",
      storyId,
      "characters",
    ] as const,
    queryFn: () =>
      httpClient.get<CharacterBundle[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/characters`,
      ),
    enabled: !!projectId && !!storyId,
    staleTime: Infinity,
  });
