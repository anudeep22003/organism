import type { ImageRecord } from "@scene-engine/shared/scene-engine.types";

export type PanelRecord = {
  id: string;
  storyId: string;
  sourceEventId: string | null;
  orderIndex: number;
  attributes: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

export type PanelBundle = {
  panel: PanelRecord;
  canonicalRender: ImageRecord | null;
  referenceImages: ImageRecord[];
};
