export type EventType =
  | "stream.start"
  | "stream.chunk"
  | "stream.end"
  | "stream.error";

export type ErrorPayload = {
  code: string;
  message: string;
  retryable: boolean;
  details: Record<string, unknown> | null;
};

export type EventEnvelope<T = unknown> = {
  schemaVersion: number;
  id: string;
  tsMs: number;
  requestId: string | null;
  streamId: string | null;
  seq: number | null;
  eventType: EventType;
  payload: T;
};