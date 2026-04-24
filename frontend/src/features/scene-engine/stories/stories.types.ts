export type StoryListItem = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string;
  meta: Record<string, unknown>;
  name: string | null;
  description: string | null;
};

export type CurrentProject = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  stories: StoryListItem[];
};
