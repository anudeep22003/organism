import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "../shared/story.constants";
import type { MyProjectType, ProjectHomeType, ProjectListEntryType } from "../shared/story.types";

export const myProjectOptions = queryOptions({
  queryKey: [...STORY_QUERY_ROOT, "projects", "me"] as const,
  queryFn: () =>
    httpClient.get<MyProjectType>(`${STORY_API_BASE}/projects/me`),
  staleTime: Infinity,
});

export const projectHomeOptions = (projectId: string) =>
  queryOptions({
    queryKey: [...STORY_QUERY_ROOT, "projects", projectId] as const,
    queryFn: () =>
      httpClient.get<ProjectHomeType>(`${STORY_API_BASE}/projects/${projectId}`),
  });

export const projectListOptions = queryOptions({
  queryKey: [...STORY_QUERY_ROOT, "projects"] as const,
  queryFn: () =>
    httpClient.get<ProjectListEntryType[]>(`${STORY_API_BASE}/projects`),
  staleTime: Infinity,
});
