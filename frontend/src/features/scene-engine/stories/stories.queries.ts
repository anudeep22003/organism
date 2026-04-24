import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "@scene-engine/core/scene-engine.constants";
import type { CurrentProject } from "./stories.types";

export const currentProjectOptions = queryOptions({
  queryKey: [...STORY_QUERY_ROOT, "projects", "me"] as const,
  queryFn: () =>
    httpClient.get<CurrentProject>(`${STORY_API_BASE}/projects/me`),
  staleTime: Infinity,
});
