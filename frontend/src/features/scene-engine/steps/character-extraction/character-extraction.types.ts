export type ImageRecord = {
  id: string;
  objectKey: string;
  bucket: string;
  contentType: string;
  width: number;
  height: number;
  sizeBytes: number;
  createdAt: string;
};

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
