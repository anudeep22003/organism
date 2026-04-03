import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { STORY_API_BASE } from "../../shared/story.constants";
import type { StoryResponseType } from "../projects.types";
import { projectHomeOptions } from "../projects.queries";

export const useAddStory = (projectId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      httpClient.post<StoryResponseType>(
        `${STORY_API_BASE}/projects/${projectId}/story`,
        { projectId },
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: projectHomeOptions(projectId).queryKey,
      }),
  });
};
