import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "@scene-engine/shared/scene-engine.constants";
import type { PanelBundle } from "./panel.types";

export const panelsOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project", projectId,
      "story", storyId,
      "panels",
    ] as const,
    queryFn: () =>
      httpClient.get<PanelBundle[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panels`,
      ),
    enabled: !!projectId && !!storyId,
    staleTime: Infinity,
  });
