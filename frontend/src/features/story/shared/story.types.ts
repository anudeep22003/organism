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

export type ProjectListEntryType = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  storyCount: number;
};

export type StoryListEntryType = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string;
  meta: Record<string, unknown>;
};

export type ProjectHomeType = ProjectListEntryType & {
  stories?: Array<StoryListEntryType>;
};
