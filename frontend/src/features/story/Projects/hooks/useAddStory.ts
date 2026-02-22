import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { StoryResponseType } from "../types";
import { projectHomeKeys } from "./useProjectHome";

const PROJECT_ENDPOINT = "/api/comic-builder/v2/projects" as const;

export const useAddStory = (projectId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      httpClient.post<StoryResponseType>(
        `${PROJECT_ENDPOINT}/${projectId}/story`,
        { projectId },
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectHomeKeys.details(projectId),
      }),
  });
};
