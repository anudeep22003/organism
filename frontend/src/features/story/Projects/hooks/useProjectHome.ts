import { httpClient } from "@/lib/httpClient";
import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ProjectHomeType } from "../types";

const PROJECT_ENDPOINT = "/api/comic-builder/v2/projects" as const;

export const projectHomeKeys = {
  all: ["project", "home"] as const,
  details: (projectId: string) =>
    [...projectHomeKeys.all, projectId] as const,
};

const getProjectHomeQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: projectHomeKeys.details(projectId),
    queryFn: () =>
      httpClient.get<ProjectHomeType>(
        `${PROJECT_ENDPOINT}/${projectId}`,
      ),
  });

export const useProjectHome = (projectId: string) => {
  return useQuery(getProjectHomeQueryOptions(projectId));
};
