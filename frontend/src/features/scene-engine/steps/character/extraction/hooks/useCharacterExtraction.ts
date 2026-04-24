import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/core/scene-engine.constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { charactersOptions } from "../../character.queries";
import { spliceCharacterIntoList, uploadReferenceImageRequest, buildHttpErrorMessage } from "../../character.utils";
import type { CharacterBundle } from "../../character.types";

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
    mutationFn: ({ characterId, file }: { characterId: string; file: File }) =>
      uploadReferenceImageRequest(projectId, storyId, characterId, file),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, (prev: CharacterBundle[] | undefined) =>
        prev ? spliceCharacterIntoList(prev, updated) : [updated],
      );
    },
  });

  const { mutate: deleteReferenceImage, isPending: isDeleting } = useMutation({
    mutationFn: ({
      characterId,
      imageId,
    }: {
      characterId: string;
      imageId: string;
    }) =>
      httpClient.delete(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/reference-image/${imageId}`,
      ),
    onSuccess: (_, { characterId, imageId }) => {
      queryClient.setQueryData(queryKey, (prev: CharacterBundle[] | undefined) =>
        prev?.map((b) =>
          b.character.id === characterId
            ? {
                ...b,
                referenceImages: b.referenceImages.filter((r) => r.id !== imageId),
              }
            : b,
        ),
      );
    },
  });

  return {
    characters,
    isLoading,
    extractCharacters,
    isExtracting,
    extractError: rawExtractError
      ? buildHttpErrorMessage(rawExtractError, {
          400: "Your story has no text yet. Go to Step 1 and write a story first.",
          404: "Story not found. Make sure a story has been created.",
        }, "Something went wrong. Try again.")
      : null,
    refineCharacter,
    isRefining,
    uploadReferenceImage,
    isUploading,
    deleteReferenceImage,
    isDeleting,
  };
}
