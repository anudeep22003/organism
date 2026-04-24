import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "@scene-engine/core/scene-engine.constants";
import type { CharacterBundle } from "./character.types";

export const charactersOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project", projectId,
      "story", storyId,
      "characters",
    ] as const,
    queryFn: () =>
      httpClient.get<CharacterBundle[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/characters`,
      ),
    enabled: !!projectId && !!storyId,
    staleTime: Infinity,
  });
