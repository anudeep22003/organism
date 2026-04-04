export type {
  StoryDetailType,
  EditEventType,
} from "@/features/scene-engine/steps/story/story.types";

export type StoryStreamChunk = {
  delta?: string;
  finishReason?: string;
};
