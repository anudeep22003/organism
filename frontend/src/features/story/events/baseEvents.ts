export type ErrorPayload = {
  code: string;
  message: string;
  retryable: boolean;
  details: Record<string, unknown> | null;
};

export type BaseEnvelope = {
  schemaVersion: number;
  id: string;
  tsMs: number;
  requestId: string | null;
  streamId: string | null;
  seq: number | null;
};

export type StreamStartEvent = BaseEnvelope & {
  eventType: "stream.start";
  payload: { delta: string };
};

export type StreamChunkEvent = BaseEnvelope & {
  eventType: "stream.chunk";
  payload: { delta: string };
};

export type StreamEndEvent = BaseEnvelope & {
  eventType: "stream.end";
  payload: { finishReason: string };
};

export type StreamErrorEvent = BaseEnvelope & {
  eventType: "stream.error";
  error: ErrorPayload;
};

export type EventEnvelope =
  | StreamStartEvent
  | StreamChunkEvent
  | StreamEndEvent
  | StreamErrorEvent;
