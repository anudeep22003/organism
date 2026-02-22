import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { projectHomeKeys } from "./useProjectHome";

const PROJECT_ENDPOINT = "/api/comic-builder/v2/projects" as const;

export const useDeleteStory = (projectId: string, storyId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      httpClient.delete(
        `${PROJECT_ENDPOINT}/${projectId}/story/${storyId}`,
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectHomeKeys.details(projectId),
      }),
  });
};
