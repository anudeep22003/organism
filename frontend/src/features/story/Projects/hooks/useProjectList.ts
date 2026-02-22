import { httpClient } from "@/lib/httpClient";
import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ProjectListEntryType } from "../types";

const PROJECT_ENDPOINT = "/api/comic-builder/v2/projects" as const;

export const projectListKeys = {
  all: ["projects"] as const,
};

export const getProjectsQueryOptions = () =>
  queryOptions({
    queryKey: projectListKeys.all,
    queryFn: () =>
      httpClient.get<ProjectListEntryType[]>(PROJECT_ENDPOINT),
    staleTime: Infinity,
  });

export const useProjectList = () => {
  return useQuery(getProjectsQueryOptions());
};
