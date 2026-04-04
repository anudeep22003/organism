import { httpClient } from "@/lib/httpClient";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { charactersOptions } from "../character-extraction.queries";

const STORY_API_BASE = "/api/comic-builder/v2" as const;

function extractionErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 400)
      return "Your story has no text yet. Go to Step 1 and write a story first.";
    if (status === 404)
      return "Story not found. Make sure a story has been created.";
  }
  return "Something went wrong. Try again.";
}

export function useCharacterExtraction(projectId: string, storyId: string) {
  const queryClient = useQueryClient();
  const queryKey = charactersOptions(projectId, storyId).queryKey;

  const { data: characters, isLoading } = useQuery(
    charactersOptions(projectId, storyId),
  );

  const {
    mutate: extractCharacters,
    isPending: isExtracting,
    error: rawExtractError,
  } = useMutation({
    mutationFn: () =>
      httpClient.post<Record<string, unknown>[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/characters`,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data);
    },
  });

  return {
    characters,
    isLoading,
    extractCharacters,
    isExtracting,
    extractError: rawExtractError
      ? extractionErrorMessage(rawExtractError)
      : null,
  };
}
