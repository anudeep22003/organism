export type ComicBuilderState = {
  phases: Phase[];
  currentPhaseIndex: number;
};

export type Phase = {
  id: string;
  name: string;
  inputText: string;
  content?: Content;
};

export type Content = {
  id: string;
  text: string;
  type: "text";
  status: "idle" | "streaming" | "completed" | "error";
};

// simple envelope that the backend sends
export type SimpleEnvelope = {
  id: string;
  ts: number;

  requestId?: string;
  streamId?: string;
  seq?: number;

  data: { delta?: string; finish_reason?: string };
};
