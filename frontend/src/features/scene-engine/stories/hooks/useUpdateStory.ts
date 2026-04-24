import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/core/scene-engine.constants";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { currentProjectOptions } from "../stories.queries";
import type { StoryListItem } from "../stories.types";

type StoryMeta = {
  tone: string;
  comicStyle: string;
  hasBackdrop: string;
  backdrop: string;
  forSomeone: string;
  relationship: string;
  feeling: string[];
};

type UpdateStoryPayload = {
  projectId: string;
  storyId: string;
  name: string;
  description: string;
  meta: StoryMeta;
};

export const useUpdateStory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, storyId, name, description, meta }: UpdateStoryPayload) =>
      httpClient.patch<StoryListItem>(
        `${STORY_API_BASE}/projects/${projectId}/story/${storyId}`,
        { name, description, meta },
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: currentProjectOptions.queryKey,
      }),
  });
};
