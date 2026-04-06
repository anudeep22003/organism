import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";

export type CharacterRecord = {
  id: string;
  name: string;
  slug: string;
  attributes: Record<string, unknown>;
  meta: Record<string, unknown>;
  sourceEventId: string | null;
  createdAt: string;
  updatedAt: string;
};

export type CharacterBundle = {
  character: CharacterRecord;
  canonicalRender: ImageRecord | null;
  referenceImages: ImageRecord[];
};
