import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useState } from "react";
import { charactersOptions } from "../../character-extraction/character-extraction.queries";
import type { CharacterBundle } from "../../character-extraction/character-extraction.types";
import { characterRendersOptions } from "../character-rendering.queries";
import type { RenderRecord } from "../character-rendering.types";

const STORY_API_BASE = "/api/comic-builder/v2" as const;

function renderErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401) return "Session expired. Please sign in again.";
    if (status === 404) return "Character not found. Try refreshing.";
  }
  return "Render failed. Try again.";
}

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
        next.set(characterId, renderErrorMessage(error));
        return next;
      });
    },
  });

  const { mutate: editRender } = useMutation({
    mutationFn: ({
      characterId,
      imageId,
      instruction,
    }: {
      characterId: string;
      imageId: string;
      instruction: string;
    }) =>
      httpClient.post<RenderRecord>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/render/edit`,
        { instruction, sourceImageId: imageId },
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
        (prev: RenderRecord[] | undefined) =>
          prev ? [newRender, ...prev] : [newRender],
      );
      void queryClient.invalidateQueries({ queryKey: charactersQueryKey });
    },
    onError: (error, { characterId }) => {
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.set(characterId, renderErrorMessage(error));
        return next;
      });
    },
  });

  return { triggerRender, renderingIds, editRender, editingIds, errorIds };
}
