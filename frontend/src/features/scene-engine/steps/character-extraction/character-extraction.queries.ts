import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";

const STORY_API_BASE = "/api/comic-builder/v2" as const;
const STORY_QUERY_ROOT = ["story"] as const;

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
      httpClient.get<Record<string, unknown>[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/characters`,
      ),
    enabled: !!projectId && !!storyId,
  });
