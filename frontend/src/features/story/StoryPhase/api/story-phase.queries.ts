import { queryOptions } from "@tanstack/react-query";
import { httpClient } from "@/lib/httpClient";
import type { ProjectDetails } from "./story-phase.types";

export const PROJECT_ENDPOINT =
  "/api/comic-builder/v2/projects" as const;

export const storyPhaseKeys = {
  all: ["storyPhase"] as const,
  project: (projectId: string) =>
    [...storyPhaseKeys.all, "project", projectId] as const,
};

export const getProjectDetailsQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: storyPhaseKeys.project(projectId),
    queryFn: () =>
      httpClient.get<ProjectDetails>(
        `${PROJECT_ENDPOINT}/${projectId}`,
      ),
    enabled: !!projectId,
  });
