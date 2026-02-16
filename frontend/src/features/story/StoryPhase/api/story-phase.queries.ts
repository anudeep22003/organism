import { queryOptions } from "@tanstack/react-query";
import { httpClient } from "@/lib/httpClient";
import { PROJECT_ENDPOINT } from "./story-phase.constants";
import { storyPhaseKeys } from "./story-phase.query-keys";
import type { ProjectDetails } from "./story-phase.types";

export const getProjectDetailsQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: storyPhaseKeys.project(projectId),
    queryFn: () =>
      httpClient.get<ProjectDetails>(
        `${PROJECT_ENDPOINT}/${projectId}`,
      ),
    enabled: !!projectId,
  });
