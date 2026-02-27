import { useCallback, useMemo, useState } from "react";
import type { PromptMessage } from "../types";
import { useStoryDetail } from "./useStoryDetail";
import { useStoryStream } from "./useStoryStream";

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
    error: storyDetail?.error,
    isGenerating,
    submitPrompt,
  };
}
