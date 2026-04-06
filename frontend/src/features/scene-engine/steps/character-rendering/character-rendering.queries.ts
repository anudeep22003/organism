import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import type { RenderRecord } from "./character-rendering.types";

const STORY_API_BASE = "/api/comic-builder/v2" as const;

export const characterRendersOptions = (
  projectId: string,
  storyId: string,
  characterId: string,
) =>
  queryOptions({
    queryKey: [
      "story",
      "project",
      projectId,
      "story",
      storyId,
      "character",
      characterId,
      "renders",
    ] as const,
    queryFn: () =>
      httpClient.get<RenderRecord[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/renders`,
      ),
    enabled: !!projectId && !!storyId && !!characterId,
  });
