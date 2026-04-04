import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import EventRouter from "../../../events/event-router";
import type { EventEnvelope } from "../../../events/base-events";
import { storyDetailOptions, storyHistoryOptions } from "../story.queries";

const STREAM_ENDPOINT = (projectId: string, storyId: string) =>
  `/api/comic-builder/v2/project/${projectId}/story/${storyId}/generate` as const;

export function useStoryStream(projectId: string, storyId: string) {
  const queryClient = useQueryClient();
  const queryKey = storyDetailOptions(projectId, storyId).queryKey;
  const eventRouter = useRef(new EventRouter(queryClient, queryKey));

  return useMutation({
    mutationFn: async (userInputText: string) => {
      const stream = httpClient.streamPost<EventEnvelope>(
        STREAM_ENDPOINT(projectId, storyId),
        { storyPrompt: userInputText },
      );
      for await (const event of stream) {
        eventRouter.current.handle(event);
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: storyHistoryOptions(projectId, storyId).queryKey,
      });
    },
  });
}
