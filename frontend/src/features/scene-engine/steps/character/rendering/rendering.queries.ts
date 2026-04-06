import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "@/features/story/shared/story.constants";
import type { ImageRecord } from "@/features/story/shared/story.types";

export const characterRendersOptions = (
  projectId: string,
  storyId: string,
  characterId: string,
) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project",
      projectId,
      "story",
      storyId,
      "character",
      characterId,
      "renders",
    ] as const,
    queryFn: () =>
      httpClient.get<ImageRecord[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/renders`,
      ),
    enabled: !!projectId && !!storyId && !!characterId,
  });
