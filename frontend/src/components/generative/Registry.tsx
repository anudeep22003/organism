import type { BaseMessage } from "@/store/useMessageStore";
import type { Actor } from "@/socket/envelopeType";
import { WriterMessage } from "./WriterMessage";
import { ClaudeMessage } from "./ClaudeMessage";
import { CodeMessage } from "./CodeMessage";

export type streamingActors = Exclude<Actor, "assistant" | "human">;

interface ActorRegistryConfig {
  label: Actor;
  component: React.ComponentType<{
    message: BaseMessage;
    onContentLoad?: () => void;
  }>;
  messageSelector: (allMessages: BaseMessage[]) => BaseMessage[];
}

export const actorRegistry: Record<
  streamingActors,
  ActorRegistryConfig
> = {
  writer: {
    label: "writer",
    component: WriterMessage,
    messageSelector: (allMessages) =>
      allMessages.filter((m) => m.type === "writer"),
  },
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
  scriptwriter: {
    label: "scriptwriter",
    component: WriterMessage,
    messageSelector: (allMessages) =>
      allMessages.filter((m) => m.type === "scriptwriter"),
  },
  director: {
    label: "director",
    component: WriterMessage,
    messageSelector: (allMessages) =>
      allMessages.filter((m) => m.type === "director"),
  },
  manager: {
    label: "manager",
    component: WriterMessage,
    messageSelector: (allMessages) =>
      allMessages.filter((m) => m.type === "manager"),
  },
};
