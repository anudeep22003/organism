export type ComicBuilderState = {
  phases: Phase[];
  currentPhaseIndex: number;
};

export type Phase = {
  id: string;
  name: string;
  inputText: string;
  content?: Content;
  payload?: object[];
};

export type Content = {
  id: string;
  text: string;
  type: "text";
  status: "idle" | "streaming" | "completed" | "error";
  payload: object[];
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

// Projects types
export type Project = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  state: Record<string, unknown>;
};

export type ProjectsState = {
  projects: Project[];
  status: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
};
