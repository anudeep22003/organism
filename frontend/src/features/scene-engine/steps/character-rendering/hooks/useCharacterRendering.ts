import { httpClient } from "@/lib/httpClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { charactersOptions } from "../../character-extraction/character-extraction.queries";
import type { CharacterBundle } from "../../character-extraction/character-extraction.types";

const STORY_API_BASE = "/api/comic-builder/v2" as const;

export function useCharacterRendering(projectId: string, storyId: string) {
  const queryClient = useQueryClient();
  const queryKey = charactersOptions(projectId, storyId).queryKey;

  const [renderingIds, setRenderingIds] = useState<Set<string>>(new Set());

  const { mutate: triggerRender } = useMutation({
    mutationFn: ({ characterId }: { characterId: string }) =>
      httpClient.post<CharacterBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/render`,
      ),
    onMutate: ({ characterId }) => {
      setRenderingIds((prev) => new Set(prev).add(characterId));
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
        queryKey,
        (prev: CharacterBundle[] | undefined) =>
          prev?.map((b) =>
            b.character.id === updated.character.id ? updated : b,
          ),
      );
    },
  });

  return { triggerRender, renderingIds };
}
