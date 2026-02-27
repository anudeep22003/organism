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
  userInputText: string[];
  meta: Record<string, unknown>;
};

export type StoryResponseType = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string[];
  meta: Record<string, unknown>;
};

export type ProjectHomeType = ProjectListEntryType & {
  stories?: Array<StoryListEntryType>;
};
