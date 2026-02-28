import { httpClient } from "@/lib/httpClient";
import { queryOptions, useQuery } from "@tanstack/react-query";
import type { EditEventType } from "../types";

const HISTORY_ENDPOINT = "/api/comic-builder/v2" as const;

export const storyHistoryKeys = {
  all: ["story", "history"] as const,
  forStory: (projectId: string, storyId: string) =>
    [...storyHistoryKeys.all, "project", projectId, "story", storyId] as const,
};

const getStoryHistoryQueryOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: storyHistoryKeys.forStory(projectId, storyId),
    queryFn: () =>
      httpClient.get<EditEventType[]>(
        `${HISTORY_ENDPOINT}/project/${projectId}/story/${storyId}/history`,
      ),
    enabled: !!projectId && !!storyId,
  });

export const useStoryHistory = (projectId: string, storyId: string) => {
  return useQuery(getStoryHistoryQueryOptions(projectId, storyId));
};
