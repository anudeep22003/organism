import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/shared/scene-engine.constants";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { panelsOptions } from "../../panel.queries";
import { splicePanelIntoList, uploadReferenceImageRequest, buildHttpErrorMessage } from "../../panel.utils";
import type { PanelBundle } from "../../panel.types";

export function usePanelExtraction(projectId: string, storyId: string) {
  const queryClient = useQueryClient();
  const queryKey = panelsOptions(projectId, storyId).queryKey;

  const { data: panels, isLoading } = useQuery(
    panelsOptions(projectId, storyId),
  );

  const {
    mutate: extractPanels,
    isPending: isExtracting,
    error: rawExtractError,
  } = useMutation({
    mutationFn: () =>
      httpClient.post<PanelBundle[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panels/generate`,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const { mutate: refinePanel, isPending: isRefining } = useMutation({
    mutationFn: ({
      panelId,
      instruction,
    }: {
      panelId: string;
      instruction: string;
    }) =>
      httpClient.post<PanelBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/refine`,
        { instruction },
      ),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, (prev: PanelBundle[] | undefined) =>
        prev ? splicePanelIntoList(prev, updated) : [updated],
      );
    },
  });

  const { mutate: uploadReferenceImage, isPending: isUploading } = useMutation({
    mutationFn: ({ panelId, file }: { panelId: string; file: File }) =>
      uploadReferenceImageRequest(projectId, storyId, panelId, file),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, (prev: PanelBundle[] | undefined) =>
        prev ? splicePanelIntoList(prev, updated) : [updated],
      );
    },
  });

  const { mutate: deleteReferenceImage, isPending: isDeleting } = useMutation({
    mutationFn: ({
      panelId,
      imageId,
    }: {
      panelId: string;
      imageId: string;
    }) =>
      httpClient.delete(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/reference-image/${imageId}`,
      ),
    onSuccess: (_, { panelId, imageId }) => {
      queryClient.setQueryData(queryKey, (prev: PanelBundle[] | undefined) =>
        prev?.map((b) =>
          b.panel.id === panelId
            ? {
                ...b,
                referenceImages: b.referenceImages.filter((r) => r.id !== imageId),
              }
            : b,
        ),
      );
    },
  });

  const { mutate: deletePanel, isPending: isDeletingPanel } = useMutation({
    mutationFn: ({ panelId }: { panelId: string }) =>
      httpClient.delete(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}`,
      ),
    onSuccess: (_, { panelId }) => {
      queryClient.setQueryData(queryKey, (prev: PanelBundle[] | undefined) =>
        prev?.filter((b) => b.panel.id !== panelId),
      );
    },
  });

  return {
    panels,
    isLoading,
    extractPanels,
    isExtracting,
    extractError: rawExtractError
      ? buildHttpErrorMessage(rawExtractError, {
          400: "Your story has no text yet. Go to Step 1 and write a story first.",
          422: "Extract characters first — panels require characters to exist.",
        }, "Something went wrong. Try again.")
      : null,
    refinePanel,
    isRefining,
    uploadReferenceImage,
    isUploading,
    deleteReferenceImage,
    isDeleting,
    deletePanel,
    isDeletingPanel,
  };
}
