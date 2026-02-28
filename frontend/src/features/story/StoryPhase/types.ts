export type StoryDetailType = {
  id: string;
  projectId: string;
  storyText: string;
  userInputText: string;
  meta: Record<string, unknown>;
  sourceEventId?: string;
  error?: string;
};

export type StoryStreamChunk = {
  delta?: string;
  finishReason?: string;
};

export type EditEventType = {
  id: string;
  projectId: string;
  targetType: string;
  targetId: string;
  operationType: string;
  userInstruction: string;
  status: string;
  createdAt: string;
};
