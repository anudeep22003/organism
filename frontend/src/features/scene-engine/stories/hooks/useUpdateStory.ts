import { httpClient } from "@/lib/httpClient";
import { myProjectOptions } from "@/features/story/projects/projects.queries";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { StoryListEntryType } from "@/features/story/shared/story.types";

const STORY_API_BASE = "/api/comic-builder/v2" as const;

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
      httpClient.patch<StoryListEntryType>(
        `${STORY_API_BASE}/projects/${projectId}/story/${storyId}`,
        { name, description, meta },
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: myProjectOptions.queryKey }),
  });
};
