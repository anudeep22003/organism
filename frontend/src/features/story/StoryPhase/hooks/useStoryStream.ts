import type { EventEnvelope } from "@/features/story/events/baseEvents";
import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import EventRouter from "../../events/eventRouter";
import { storyDetailKeys } from "./useStoryDetail";

const STREAM_ENDPOINT = (storyId: string) =>
  `/api/comic-builder/v2/story/${storyId}/generate` as const;

export const useStoryStream = (projectId: string, storyId: string) => {
  const queryClient = useQueryClient();
  const queryKey = storyDetailKeys.detail(projectId, storyId);
  const eventRouter = useRef(new EventRouter(queryClient, queryKey));

  const mutation = useMutation({
    mutationFn: (userInputText: string) =>
      startGeneration(userInputText, storyId),
  });

  async function startGeneration(
    userInputText: string,
    storyId: string,
  ) {
    const stream = httpClient.streamPost<EventEnvelope>(
      STREAM_ENDPOINT(storyId),
      { storyPrompt: userInputText },
    );

    for await (const event of stream) {
      eventRouter.current.handle(event);
    }
  }

  return mutation;
};
