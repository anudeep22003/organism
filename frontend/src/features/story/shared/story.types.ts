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
  name: string | null;
  description: string | null;
};

export type ProjectHomeType = ProjectListEntryType & {
  stories?: Array<StoryListEntryType>;
};

export type MyProjectType = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  state: Record<string, unknown>;
  stories: StoryListEntryType[];
};
