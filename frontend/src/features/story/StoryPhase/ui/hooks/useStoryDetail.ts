import { httpClient } from "@/lib/httpClient";
import { queryOptions, useQuery } from "@tanstack/react-query";
import type { StoryDetailType } from "../../api/story-phase.types";

const STORY_ENDPOINT = "/api/comic-builder/v2" as const;

export const storyDetailKeys = {
  all: ["story", "detail"] as const,
  detail: (projectId: string, storyId: string) =>
    [...storyDetailKeys.all, "project", projectId, "story", storyId] as const,
};

const getStoryDetailQueryOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: storyDetailKeys.detail(projectId, storyId),
    queryFn: () =>
      httpClient.get<StoryDetailType>(
        `${STORY_ENDPOINT}/project/${projectId}/story/${storyId}`,
      ),
    enabled: !!projectId && !!storyId,
  });

export const useStoryDetail = (projectId: string, storyId: string) => {
  return useQuery(getStoryDetailQueryOptions(projectId, storyId));
};
