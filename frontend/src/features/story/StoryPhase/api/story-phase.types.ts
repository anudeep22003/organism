export type ProjectDetails = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  storyCount: number;
  stories?: StoryEntry[];
  characters?: Record<string, unknown>[];
  panels?: Record<string, unknown>[];
};

export type StoryEntry = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string[];
  meta: Record<string, unknown>;
};

export type StoryStreamChunk = {
  text: string;
  done?: boolean;
};

export type PromptMessage = {
  id: string;
  text: string;
  timestamp: number;
};
