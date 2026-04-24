import { isAxiosError } from "axios";
import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@scene-engine/core/scene-engine.constants";
import type { CharacterBundle } from "./character.types";

export function spliceCharacterIntoList(
  list: CharacterBundle[],
  updated: CharacterBundle,
): CharacterBundle[] {
  return list.map((b) =>
    b.character.id === updated.character.id ? updated : b,
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
  characterId: string,
  file: File,
): Promise<CharacterBundle> {
  const formData = new FormData();
  formData.append("image", file);
  return httpClient.post<CharacterBundle>(
    `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/upload-reference-image`,
    formData,
  );
}
