import type { QueryClient } from "@tanstack/react-query";
import type { StoryStreamChunk } from "../StoryPhase/api/story-phase.types";
import type { EventEnvelope } from "./baseEvents";

class EventRouter {
  private queryClient: QueryClient;

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
  }

  handle(event: EventEnvelope<StoryStreamChunk>) {
    switch (event.eventType) {
      case "stream.start":
        this.handleStreamStart(event);
        break;
      case "stream.chunk":
        this.handleStreamChunk(event);
        break;
      case "stream.end":
        this.handleStreamEnd(event);
        break;
    }
  }

  private handleStreamStart(event: EventEnvelope<StoryStreamChunk>) {
    this.queryClient.setQueryData(
      ["batman"],
      () => `stream started: ${event.payload.delta}`,
    );
  }

  private handleStreamChunk(event: EventEnvelope<StoryStreamChunk>) {
    this.queryClient.setQueryData(
      ["batman"],
      (old: string) => old + (event.payload.delta ?? ""),
    );
  }

  private handleStreamEnd(event: EventEnvelope<StoryStreamChunk>) {
    this.queryClient.setQueryData(
      ["batman"],
      (old: string) => old + (event.payload.finishReason ?? ""),
    );
  }
}

export default EventRouter;
