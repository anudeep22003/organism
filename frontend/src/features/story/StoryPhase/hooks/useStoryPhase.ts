import { useCallback } from "react";
import { useStoryDetail } from "./useStoryDetail";
import { useStoryStream } from "./useStoryStream";

export function useStoryPhase(projectId: string, storyId: string) {
  const { mutate: generate, isPending: isGenerating } =
    useStoryStream(projectId, storyId);

  const { data: storyDetail } = useStoryDetail(projectId, storyId);

  const submitPrompt = useCallback(
    (text: string) => {
      generate(text);
    },
    [generate],
  );

  return {
    storyText: storyDetail?.storyText ?? "",
    error: storyDetail?.error,
    isGenerating,
    submitPrompt,
  };
}
