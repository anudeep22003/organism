import { httpClient } from "@/lib/httpClient";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { charactersOptions } from "../character-extraction.queries";
import type { CharacterBundle } from "../character-extraction.types";

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

function spliceCharacterIntoList(
  list: CharacterBundle[],
  updated: CharacterBundle,
): CharacterBundle[] {
  return list.map((b) =>
    b.character.id === updated.character.id ? updated : b,
  );
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
      httpClient.post<CharacterBundle[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/characters`,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const { mutate: refineCharacter, isPending: isRefining } = useMutation({
    mutationFn: ({
      characterId,
      instruction,
    }: {
      characterId: string;
      instruction: string;
    }) =>
      httpClient.post<CharacterBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/refine`,
        { instruction },
      ),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, (prev: CharacterBundle[] | undefined) =>
        prev ? spliceCharacterIntoList(prev, updated) : [updated],
      );
    },
  });

  const { mutate: uploadReferenceImage, isPending: isUploading } = useMutation({
    mutationFn: ({ characterId, file }: { characterId: string; file: File }) => {
      const formData = new FormData();
      formData.append("image", file);
      return httpClient.post<CharacterBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/upload-reference-image`,
        formData,
      );
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, (prev: CharacterBundle[] | undefined) =>
        prev ? spliceCharacterIntoList(prev, updated) : [updated],
      );
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
    refineCharacter,
    isRefining,
    uploadReferenceImage,
    isUploading,
  };
}
