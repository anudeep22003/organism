import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@/features/story/shared/story.constants";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { charactersOptions } from "../../character.queries";
import { spliceCharacterIntoList, uploadReferenceImageRequest, buildHttpErrorMessage } from "../../character.utils";
import type { CharacterBundle } from "../../character.types";
import type { ImageRecord } from "@/features/story/shared/story.types";
import { characterRendersOptions } from "../rendering.queries";

export function useCharacterRendering(projectId: string, storyId: string) {
  const queryClient = useQueryClient();
  const charactersQueryKey = charactersOptions(projectId, storyId).queryKey;

  const [renderingIds, setRenderingIds] = useState<Set<string>>(new Set());
  const [editingIds, setEditingIds] = useState<Set<string>>(new Set());
  const [errorIds, setErrorIds] = useState<Map<string, string>>(new Map());

  const { mutate: triggerRender } = useMutation({
    mutationFn: ({ characterId }: { characterId: string }) =>
      httpClient.post<CharacterBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/render`,
      ),
    onMutate: ({ characterId }) => {
      setRenderingIds((prev) => new Set(prev).add(characterId));
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.delete(characterId);
        return next;
      });
    },
    onSettled: (_, __, { characterId }) => {
      setRenderingIds((prev) => {
        const next = new Set(prev);
        next.delete(characterId);
        return next;
      });
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(
        charactersQueryKey,
        (prev: CharacterBundle[] | undefined) =>
          prev?.map((b) =>
            b.character.id === updated.character.id ? updated : b,
          ),
      );
    },
    onError: (error, { characterId }) => {
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.set(characterId, buildHttpErrorMessage(error, {
          401: "Session expired. Please sign in again.",
          404: "Character not found. Try refreshing.",
        }, "Render failed. Try again."));
        return next;
      });
    },
  });

  const { mutateAsync: uploadReferenceImage, isPending: isUploading } = useMutation({
    mutationFn: ({ characterId, file }: { characterId: string; file: File }) =>
      uploadReferenceImageRequest(projectId, storyId, characterId, file),
    onSuccess: (updated) => {
      queryClient.setQueryData(charactersQueryKey, (prev: CharacterBundle[] | undefined) =>
        prev ? spliceCharacterIntoList(prev, updated) : [updated],
      );
    },
  });

  const { mutate: editRender } = useMutation({
    mutationFn: ({
      characterId,
      imageId,
      instruction,
      referenceImageId,
    }: {
      characterId: string;
      imageId: string;
      instruction: string;
      referenceImageId?: string;
    }) =>
      httpClient.post<ImageRecord>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/render/edit`,
        {
          instruction,
          sourceImageId: imageId,
          ...(referenceImageId ? { referenceImageId } : {}),
        },
      ),
    onMutate: ({ characterId }) => {
      setEditingIds((prev) => new Set(prev).add(characterId));
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.delete(characterId);
        return next;
      });
    },
    onSettled: (_, __, { characterId }) => {
      setEditingIds((prev) => {
        const next = new Set(prev);
        next.delete(characterId);
        return next;
      });
    },
    onSuccess: (newRender, { characterId }) => {
      queryClient.setQueryData(
        characterRendersOptions(projectId, storyId, characterId).queryKey,
        (prev: ImageRecord[] | undefined) =>
          prev ? [newRender, ...prev] : [newRender],
      );
      void queryClient.invalidateQueries({ queryKey: charactersQueryKey });
    },
    onError: (error, { characterId }) => {
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.set(characterId, buildHttpErrorMessage(error, {
          401: "Session expired. Please sign in again.",
          404: "Character not found. Try refreshing.",
        }, "Render failed. Try again."));
        return next;
      });
    },
  });

  const { mutate: setCanonicalRender, isPending: isSettingCanonical } = useMutation({
    mutationFn: ({ characterId, imageId }: { characterId: string; imageId: string }) =>
      httpClient.post<CharacterBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/set-canonical-render`,
        { imageId },
      ),
    onSuccess: (updatedBundle) => {
      queryClient.setQueryData(
        charactersQueryKey,
        (prev: CharacterBundle[] | undefined) =>
          prev?.map((b) =>
            b.character.id === updatedBundle.character.id ? updatedBundle : b,
          ),
      );
    },
  });

  return { triggerRender, renderingIds, uploadReferenceImage, isUploading, editRender, editingIds, setCanonicalRender, isSettingCanonical, errorIds };
}
