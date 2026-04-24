import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/shared/scene-engine.constants";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { currentProjectOptions } from "../stories.queries";

type DeleteStoryPayload = {
  projectId: string;
  storyId: string;
};

export const useDeleteStory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, storyId }: DeleteStoryPayload) =>
      httpClient.delete(
        `${STORY_API_BASE}/projects/${projectId}/story/${storyId}`,
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: currentProjectOptions.queryKey,
      }),
  });
};
