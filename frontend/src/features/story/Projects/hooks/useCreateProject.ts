import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ProjectListEntryType } from "../types";
import { projectListKeys } from "./useProjectList";

const PROJECT_ENDPOINT = "/api/comic-builder/v2/projects" as const;

type CreateProjectPayload = {
  name: string;
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateProjectPayload) =>
      httpClient.post<ProjectListEntryType>(PROJECT_ENDPOINT, payload),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: projectListKeys.all }),
  });
};
