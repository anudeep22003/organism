export type StoryDetailType = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string[];
  meta: Record<string, unknown>;
};

export type StoryStreamChunk = {
  delta?: string;
  finishReason?: string;
};

export type PromptMessage = {
  id: string;
  text: string;
  timestamp: number;
};
