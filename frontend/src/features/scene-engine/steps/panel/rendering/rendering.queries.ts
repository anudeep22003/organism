import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "@scene-engine/core/scene-engine.constants";
import type { ImageRecord } from "@scene-engine/core/scene-engine.types";

export const panelRendersOptions = (
  projectId: string,
  storyId: string,
  panelId: string,
) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project", projectId,
      "story", storyId,
      "panel", panelId,
      "renders",
    ] as const,
    queryFn: () =>
      httpClient.get<ImageRecord[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/renders`,
      ),
    enabled: !!projectId && !!storyId && !!panelId,
  });
