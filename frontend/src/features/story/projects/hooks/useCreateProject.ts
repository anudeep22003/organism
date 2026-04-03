import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { STORY_API_BASE } from "../../shared/story.constants";
import type { ProjectListEntryType } from "../../shared/story.types";
import { projectListOptions } from "../projects.queries";

type CreateProjectPayload = {
  name: string;
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateProjectPayload) =>
      httpClient.post<ProjectListEntryType>(
        `${STORY_API_BASE}/projects`,
        payload,
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: projectListOptions.queryKey }),
  });
};
