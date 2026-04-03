import type { QueryClient } from "@tanstack/react-query";
import type { StoryDetailType } from "../phases/story-phase/story-phase.types";
import type {
  EventEnvelope,
  StreamChunkEvent,
  StreamErrorEvent,
} from "./base-events";

class EventRouter {
  private queryClient: QueryClient;
  private queryKey: readonly unknown[];

  constructor(queryClient: QueryClient, queryKey: readonly unknown[]) {
    this.queryClient = queryClient;
    this.queryKey = queryKey;
  }

  handle(event: EventEnvelope) {
    switch (event.eventType) {
      case "stream.start":
        this.handleStreamStart();
        break;
      case "stream.chunk":
        this.handleStreamChunk(event);
        break;
      case "stream.error":
        this.handleStreamError(event);
        break;
      case "stream.end":
        break;
    }
  }

  private handleStreamStart() {
    this.queryClient.setQueryData<StoryDetailType>(
      this.queryKey,
      (old) => (old ? { ...old, storyText: "", error: undefined } : undefined),
    );
  }

  private handleStreamChunk(event: StreamChunkEvent) {
    this.queryClient.setQueryData<StoryDetailType>(
      this.queryKey,
      (old) =>
        old
          ? {
              ...old,
              storyText: old.storyText + (event.payload.delta ?? ""),
            }
          : undefined,
    );
  }

  private handleStreamError(event: StreamErrorEvent) {
    this.queryClient.setQueryData<StoryDetailType>(
      this.queryKey,
      (old) =>
        old
          ? {
              ...old,
              error: event.error.message,
            }
          : undefined,
    );
  }
}

export default EventRouter;
