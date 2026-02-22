import type { QueryClient } from "@tanstack/react-query";
import type { StoryDetailType } from "../StoryPhase/types";
import type { StoryStreamChunk } from "../StoryPhase/types";
import type { EventEnvelope } from "./baseEvents";

class EventRouter {
  private queryClient: QueryClient;
  private queryKey: readonly unknown[];

  constructor(queryClient: QueryClient, queryKey: readonly unknown[]) {
    this.queryClient = queryClient;
    this.queryKey = queryKey;
  }

  handle(event: EventEnvelope<StoryStreamChunk>) {
    switch (event.eventType) {
      case "stream.start":
        this.handleStreamStart();
        break;
      case "stream.chunk":
        this.handleStreamChunk(event);
        break;
      case "stream.end":
        break;
    }
  }

  private handleStreamStart() {
    this.queryClient.setQueryData<StoryDetailType>(
      this.queryKey,
      (old) => (old ? { ...old, storyText: "" } : undefined),
    );
  }

  private handleStreamChunk(event: EventEnvelope<StoryStreamChunk>) {
    this.queryClient.setQueryData<StoryDetailType>(
      this.queryKey,
      (old) =>
        old
          ? { ...old, storyText: old.storyText + (event.payload.delta ?? "") }
          : undefined,
    );
  }
}

export default EventRouter;
