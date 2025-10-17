import type { BaseMessage } from "@/store/useMessageStore";
import {
  ACTORS,
  type Actor,
  type StreamingActors,
} from "@/socket/envelopeType";
import { WriterMessage } from "./WriterMessage";
import { ClaudeMessage } from "./ClaudeMessage";
import { CodeMessage } from "./CodeMessage";

interface ActorRegistryConfig {
  label: Actor;
  component: React.ComponentType<{
    message: BaseMessage;
    onContentLoad?: () => void;
  }>;
  messageSelector: (allMessages: BaseMessage[]) => BaseMessage[];
}

// Create a helper function to reduce repetition
const createActorConfig = (actor: Actor): ActorRegistryConfig => ({
  label: actor,
  component: WriterMessage,
  messageSelector: (allMessages: BaseMessage[]) =>
    allMessages.filter((m: BaseMessage) => m.type === actor),
});

// Much cleaner default registry
const defaultActorRegistry: Record<Actor, ActorRegistryConfig> =
  Object.fromEntries(
    ACTORS.map((actor) => [actor, createActorConfig(actor)])
  ) as Record<Actor, ActorRegistryConfig>;

// Now override only what you need
export const actorRegistry: Record<
  StreamingActors,
  ActorRegistryConfig
> = {
  ...defaultActorRegistry,
  claude: {
    label: "claude",
    component: ClaudeMessage,
    messageSelector: (allMessages) =>
      allMessages.filter((m) => m.type === "claude"),
  },
  coder: {
    label: "coder",
    component: CodeMessage,
    messageSelector: (allMessages) =>
      allMessages.filter((m) => m.type === "coder"),
  },
};
