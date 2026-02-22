import type { EventEnvelope } from "@/features/story/events/baseEvents";
import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useRef, useState } from "react";
import EventRouter from "../../../events/eventRouter";
import type {
  PromptMessage,
  StoryStreamChunk,
} from "../../api/story-phase.types";
import { storyDetailKeys, useStoryDetail } from "./useStoryDetail";

const STREAM_ENDPOINT = (storyId: string) =>
  `/api/comic-builder/v2/story/${storyId}/generate` as const;

const useStoryStream = (projectId: string, storyId: string) => {
  const queryClient = useQueryClient();
  const queryKey = storyDetailKeys.detail(projectId, storyId);
  const eventRouter = useRef(new EventRouter(queryClient, queryKey));

  const mutation = useMutation({
    mutationFn: (userInputText: string) =>
      startGeneration(userInputText, storyId),
  });

  async function startGeneration(userInputText: string, storyId: string) {
    const stream = httpClient.streamPost<EventEnvelope<StoryStreamChunk>>(
      STREAM_ENDPOINT(storyId),
      { storyPrompt: userInputText },
    );

    for await (const event of stream) {
      eventRouter.current.handle(event);
    }
  }

  return mutation;
};

export function useStoryPhase(projectId: string, storyId: string) {
  const [sessionMessages, setSessionMessages] = useState<PromptMessage[]>([]);
  const { mutate: generate, isPending: isGenerating } =
    useStoryStream(projectId, storyId);

  const { data: storyDetail } = useStoryDetail(projectId, storyId);

  // Synthetic id and null timestamp. 
  // CONSIDER: storing richer userinputtext in the db not just as strings
  const pastMessages: PromptMessage[] = useMemo(
    () =>
      (storyDetail?.userInputText ?? []).map((text, index) => ({
        id: `past-${index}`,
        text,
        timestamp: 0,
      })),
    [storyDetail?.userInputText],
  );

  const submitPrompt = useCallback(
    (text: string) => {
      const message: PromptMessage = {
        id: crypto.randomUUID(),
        text,
        timestamp: Date.now(),
      };
      setSessionMessages((prev) => [...prev, message]);
      generate(text);
    },
    [generate],
  );

  return {
    messages: [...pastMessages, ...sessionMessages],
    storyText: storyDetail?.storyText ?? "",
    isGenerating,
    submitPrompt,
  };
}
