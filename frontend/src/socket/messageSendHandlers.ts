import type { Actor, Envelope } from "@/socket/envelopeType";
import {
  constructChatStreamMessages,
  prepareCodeMessage,
} from "@/lib/messageUtils";
import type { TypedMessage } from "@/store/useMessageStore";

type EmitCallback = (
  event: string,
  data: unknown,
  callback?: (ack: string) => void
) => void;
type AddMessage = (message: TypedMessage) => void;
type CreateStreamMessage = (
  streamId: string,
  requestId: string,
  actor: Actor
) => void;

const createHumanMessage = (inputText: string): TypedMessage => ({
  id: `human-${Date.now()}`,
  ts: new Date().getTime(),
  content: inputText,
  type: "human",
});

const createStreamStartEnvelope = <T>(
  actor: Actor,
  data: T
): Envelope<T> => ({
  v: "1",
  id: `human-${Date.now()}`,
  ts: new Date().getTime(),
  requestId: crypto.randomUUID(),
  direction: "c2s",
  actor,
  action: "stream",
  modifier: "start",
  data,
});

const handleStreamAck = (
  ack: string,
  actor: Actor,
  createStreamMessage: CreateStreamMessage
) => {
  console.log("ack", ack);
  const { streamId, requestId } = JSON.parse(ack) as {
    streamId: string;
    requestId: string;
  };
  createStreamMessage(streamId, requestId, actor);
};

export const sendCodeMessage = async (
  inputText: string,
  setInputText: (text: string) => void,
  emit: EmitCallback,
  addMessage: AddMessage,
  humanAreaMessages: TypedMessage[],
  createStreamMessage: CreateStreamMessage
) => {
  const humanMessage = createHumanMessage(inputText);
  addMessage(humanMessage);

  const history = constructChatStreamMessages(humanAreaMessages);
  const codeRequest = await prepareCodeMessage(inputText);
  const data = { history, codeRequest };
  const envelope = createStreamStartEnvelope("coder", data);

  setInputText("");

  emit(`c2s.coder.stream.start`, envelope, (ack) =>
    handleStreamAck(ack, "coder", createStreamMessage)
  );
};

export const sendChatMessage = async (
  inputText: string,
  setInputText: (text: string) => void,
  emit: EmitCallback,
  addMessage: AddMessage,
  humanAreaMessages: TypedMessage[],
  createStreamMessage: CreateStreamMessage
) => {
  if (!inputText.trim()) return;

  const humanMessage = createHumanMessage(inputText);
  addMessage(humanMessage);

  const history = [
    ...constructChatStreamMessages(humanAreaMessages),
    { role: "user", content: inputText },
  ];
  const data = { history };

  const envelope = createStreamStartEnvelope("assistant", data);

  setInputText("");

  emit(`c2s.assistant.stream.start`, envelope, (ack) =>
    handleStreamAck(ack, "assistant", createStreamMessage)
  );
};

export const sendWriterMessage = async (
  _inputText: string,
  setInputText: (text: string) => void,
  emit: EmitCallback,
  _addMessage: AddMessage,
  humanAreaMessages: TypedMessage[],
  createStreamMessage: CreateStreamMessage
) => {
  const data = {
    history: constructChatStreamMessages(humanAreaMessages),
  };

  const envelope = createStreamStartEnvelope("writer", data);

  setInputText("");

  emit(`c2s.writer.stream.start`, envelope, (ack) =>
    handleStreamAck(ack, "writer", createStreamMessage)
  );
};

export const sendClaudeMessage = async (
  _inputText: string,
  setInputText: (text: string) => void,
  emit: EmitCallback,
  _addMessage: AddMessage,
  _humanAreaMessages: TypedMessage[],
  createStreamMessage: CreateStreamMessage
) => {
  const data = {
    query: `
    Now set up a websocket server with fastapi. It is a dummy server which just streams the sentence 
      "Twinkle twinkle little star,
      How I wonder what you are,
      Up above the world so high,
      Like a diamond in the sky.
      When the blazing sun is gone,
      When he nothing shines upon,
      Then you show your little light,
      Twinkle, twinkle, all the night."

      Split the sentence into words and stream them one by one with a sleep of 0.2 seconds.

      The websocket server should be able to handle multiple clients.

      Make this a separate router. 
      Integrate it with the main fastapi router.
      `,
  };

  const envelope = createStreamStartEnvelope("claude", data);

  setInputText("");

  emit(`c2s.claude.stream.start`, envelope, (ack) =>
    handleStreamAck(ack, "claude", createStreamMessage)
  );
};

export const sendDirectorMessage = async (
  inputText: string,
  setInputText: (text: string) => void,
  emit: EmitCallback,
  addMessage: AddMessage,
  _humanAreaMessages: TypedMessage[],
  _createStreamMessage: CreateStreamMessage
) => {
  if (!inputText.trim()) return;

  const humanMessage = createHumanMessage(inputText);
  addMessage(humanMessage);

  const data = { prompt: inputText };

  const envelope = createStreamStartEnvelope("director", data);
  setInputText("");
  emit(`c2s.director.stream.start`, envelope);
};
