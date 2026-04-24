import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "../shared/story.constants";
import type { MyProjectType } from "../shared/story.types";

export const myProjectOptions = queryOptions({
  queryKey: [...STORY_QUERY_ROOT, "projects", "me"] as const,
  queryFn: () =>
    httpClient.get<MyProjectType>(`${STORY_API_BASE}/projects/me`),
  staleTime: Infinity,
});
