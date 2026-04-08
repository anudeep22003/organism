import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { STORY_API_BASE } from "../../shared/story.constants";
import type { StoryListEntryType } from "../../shared/story.types";
import { myProjectOptions } from "../projects.queries";

type StoryMeta = {
  tone: string;
  comicStyle: string;
  hasBackdrop: string;
  backdrop: string;
  forSomeone: string;
  relationship: string;
  feeling: string[];
};

type CreateStoryPayload = {
  projectId: string;
  name: string;
  description: string;
  meta: StoryMeta;
};

export const useCreateStory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, name, description, meta }: CreateStoryPayload) =>
      httpClient.post<StoryListEntryType>(
        `${STORY_API_BASE}/projects/${projectId}/story`,
        { name, description, meta },
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: myProjectOptions.queryKey }),
  });
};
