import type { EventEnvelope } from "@/features/story/events/baseEvents";
import { httpClient } from "@/lib/httpClient";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import EventRouter from "../../../events/eventRouter";
import type {
  PromptMessage,
  StoryStreamChunk,
} from "../../api/story-phase.types";

export const STREAM_ENDPOINT = (storyId: string) =>
  `/api/comic-builder/v2/story/${storyId}/generate` as const;

const useStoryStream = (storyId: string) => {
  const queryClient = useQueryClient();
  const eventRouter = useRef(new EventRouter(queryClient));

  const mutation = useMutation({
    mutationFn: (userInputText: string) =>
      startGeneration(userInputText, storyId),
  });

  async function startGeneration(userInputText: string, storyId: string) {
    queryClient.setQueryData(["batman"], () => "");

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

export function useStoryPhase(storyId: string) {
  const [messages, setMessages] = useState<PromptMessage[]>([]);
  const { mutate: generate, isPending: isGenerating } =
    useStoryStream(storyId);

  const { data: storyTextRaw } = useQuery<string | undefined>({
    queryKey: ["batman"],
    queryFn: () => Promise.resolve(undefined),
  });

  const submitPrompt = useCallback(
    (text: string) => {
      const message: PromptMessage = {
        id: crypto.randomUUID(),
        text,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, message]);
      generate(text);
    },
    [generate],
  );

  return {
    messages,
    storyText: storyTextRaw ?? "",
    isGenerating,
    submitPrompt,
  };
}
