export type StoryListEntryType = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string;
  meta: Record<string, unknown>;
  name: string | null;
  description: string | null;
};

export type MyProjectType = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  stories: StoryListEntryType[];
};
