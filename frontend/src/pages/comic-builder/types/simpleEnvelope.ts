// simple envelope that the backend sends
export type SimpleEnvelope = {
  id: string;
  ts: number;

  requestId?: string;
  streamId?: string;
  seq?: number;

  data: { delta?: string; finish_reason?: string; error?: string };
};
