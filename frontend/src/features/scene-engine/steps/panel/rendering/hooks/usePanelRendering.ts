import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/core/scene-engine.constants";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { panelsOptions } from "../../panel.queries";
import { splicePanelIntoList, uploadReferenceImageRequest, buildHttpErrorMessage } from "../../panel.utils";
import type { PanelBundle } from "../../panel.types";
import type { ImageRecord } from "@scene-engine/core/scene-engine.types";
import { panelRendersOptions } from "../rendering.queries";

export function usePanelRendering(projectId: string, storyId: string) {
  const queryClient = useQueryClient();
  const panelsQueryKey = panelsOptions(projectId, storyId).queryKey;

  const [renderingIds, setRenderingIds] = useState<Set<string>>(new Set());
  const [editingIds, setEditingIds] = useState<Set<string>>(new Set());
  const [errorIds, setErrorIds] = useState<Map<string, string>>(new Map());

  const { mutate: triggerRender } = useMutation({
    mutationFn: ({ panelId }: { panelId: string }) =>
      httpClient.post<PanelBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/render`,
      ),
    onMutate: ({ panelId }) => {
      setRenderingIds((prev) => new Set(prev).add(panelId));
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.delete(panelId);
        return next;
      });
    },
    onSettled: (_, __, { panelId }) => {
      setRenderingIds((prev) => {
        const next = new Set(prev);
        next.delete(panelId);
        return next;
      });
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(
        panelsQueryKey,
        (prev: PanelBundle[] | undefined) =>
          prev ? splicePanelIntoList(prev, updated) : [updated],
      );
    },
    onError: (error, { panelId }) => {
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.set(panelId, buildHttpErrorMessage(error, {
          401: "Session expired. Please sign in again.",
          404: "Panel not found. Try refreshing.",
        }, "Render failed. Try again."));
        return next;
      });
    },
  });

  const { mutateAsync: uploadReferenceImage, isPending: isUploading } = useMutation({
    mutationFn: ({ panelId, file }: { panelId: string; file: File }) =>
      uploadReferenceImageRequest(projectId, storyId, panelId, file),
    onSuccess: (updated) => {
      queryClient.setQueryData(panelsQueryKey, (prev: PanelBundle[] | undefined) =>
        prev ? splicePanelIntoList(prev, updated) : [updated],
      );
    },
  });

  const { mutate: editRender } = useMutation({
    mutationFn: ({
      panelId,
      imageId,
      instruction,
      referenceImageId,
    }: {
      panelId: string;
      imageId: string;
      instruction: string;
      referenceImageId?: string;
    }) =>
      httpClient.post<ImageRecord>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/render/edit`,
        {
          instruction,
          sourceImageId: imageId,
          ...(referenceImageId ? { referenceImageId } : {}),
        },
      ),
    onMutate: ({ panelId }) => {
      setEditingIds((prev) => new Set(prev).add(panelId));
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.delete(panelId);
        return next;
      });
    },
    onSettled: (_, __, { panelId }) => {
      setEditingIds((prev) => {
        const next = new Set(prev);
        next.delete(panelId);
        return next;
      });
    },
    onSuccess: (newRender, { panelId }) => {
      queryClient.setQueryData(
        panelRendersOptions(projectId, storyId, panelId).queryKey,
        (prev: ImageRecord[] | undefined) =>
          prev ? [newRender, ...prev] : [newRender],
      );
      void queryClient.invalidateQueries({ queryKey: panelsQueryKey });
    },
    onError: (error, { panelId }) => {
      setErrorIds((prev) => {
        const next = new Map(prev);
        next.set(panelId, buildHttpErrorMessage(error, {
          401: "Session expired. Please sign in again.",
          404: "Panel not found. Try refreshing.",
        }, "Render failed. Try again."));
        return next;
      });
    },
  });

  const { mutate: setCanonicalRender, isPending: isSettingCanonical } = useMutation({
    mutationFn: ({ panelId, imageId }: { panelId: string; imageId: string }) =>
      httpClient.post<PanelBundle>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/set-canonical-render`,
        { imageId },
      ),
    onSuccess: (updatedBundle) => {
      queryClient.setQueryData(
        panelsQueryKey,
        (prev: PanelBundle[] | undefined) =>
          prev ? splicePanelIntoList(prev, updatedBundle) : [updatedBundle],
      );
    },
  });

  return { triggerRender, renderingIds, uploadReferenceImage, isUploading, editRender, editingIds, setCanonicalRender, isSettingCanonical, errorIds };
}
