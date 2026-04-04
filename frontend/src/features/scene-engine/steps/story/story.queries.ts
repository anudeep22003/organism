import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import type { EditEventType, StoryDetailType } from "./story.types";

const STORY_API_BASE = "/api/comic-builder/v2" as const;
const STORY_QUERY_ROOT = ["story"] as const;

export const storyDetailOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project",
      projectId,
      "story",
      storyId,
    ] as const,
    queryFn: () =>
      httpClient.get<StoryDetailType>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}`,
      ),
    enabled: !!projectId && !!storyId,
  });

export const storyHistoryOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project",
      projectId,
      "story",
      storyId,
      "history",
    ] as const,
    queryFn: () =>
      httpClient.get<EditEventType[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/history`,
      ),
    enabled: !!projectId && !!storyId,
  });
