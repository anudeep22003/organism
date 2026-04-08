import { httpClient } from "@/lib/httpClient";
import { myProjectOptions } from "@/features/story/projects/projects.queries";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const STORY_API_BASE = "/api/comic-builder/v2" as const;

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
      queryClient.invalidateQueries({ queryKey: myProjectOptions.queryKey }),
  });
};
