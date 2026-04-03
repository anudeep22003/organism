import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { STORY_API_BASE } from "../../shared/story.constants";
import { projectHomeOptions } from "../projects.queries";

export const useDeleteStory = (projectId: string, storyId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      httpClient.delete(
        `${STORY_API_BASE}/projects/${projectId}/story/${storyId}`,
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectHomeOptions(projectId).queryKey,
      }),
  });
};
