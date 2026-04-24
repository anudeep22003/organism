import { isAxiosError } from "axios";
import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/core/scene-engine.constants";
import type { PanelBundle } from "./panel.types";

export function splicePanelIntoList(
  list: PanelBundle[],
  updated: PanelBundle,
): PanelBundle[] {
  return list.map((b) =>
    b.panel.id === updated.panel.id ? updated : b,
  );
}

export function buildHttpErrorMessage(
  error: unknown,
  statusMessages: Record<number, string>,
  fallback: string,
): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    if (status && statusMessages[status]) return statusMessages[status];
  }
  return fallback;
}

export async function uploadReferenceImageRequest(
  projectId: string,
  storyId: string,
  panelId: string,
  file: File,
): Promise<PanelBundle> {
  const formData = new FormData();
  formData.append("image", file);
  return httpClient.post<PanelBundle>(
    `${STORY_API_BASE}/project/${projectId}/story/${storyId}/panel/${panelId}/upload-reference-image`,
    formData,
  );
}
