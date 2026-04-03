import { useQuery } from "@tanstack/react-query";
import { useCallback } from "react";
import { storyDetailOptions } from "../story-phase.queries";
import { useStoryStream } from "./useStoryStream";

export function useStoryPhase(projectId: string, storyId: string) {
  const { mutate: generate, isPending: isGenerating } =
    useStoryStream(projectId, storyId);

  const { data: storyDetail } = useQuery(
    storyDetailOptions(projectId, storyId),
  );

  const submitPrompt = useCallback(
    (text: string) => {
      generate(text);
    },
    [generate],
  );

  return {
    storyText: storyDetail?.storyText ?? "",
    userInputText: storyDetail?.userInputText ?? "",
    error: storyDetail?.error,
    isGenerating,
    submitPrompt,
  };
}
