// Comic State types - matches backend state.py
export type ContentStatus =
  | "idle"
  | "streaming"
  | "completed"
  | "error";

// Generic payload item - keys are strings, values are string or string[]
export type PayloadItem = Record<string, string | string[]>;

export type ComicContent = {
  id: string;
  text: string;
  type: "text";
  status: ContentStatus;
  payload: PayloadItem[];
};

export type ComicPhase = {
  id: string;
  name: string;
  inputText: string;
  content: ComicContent | null;
};

export type ComicState = {
  phases: ComicPhase[];
  currentPhaseIndex: number;
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
  state: ComicState;
};

export type ProjectsState = {
  projects: Project[];
  currentProject: Project | null;
  status: "idle" | "loading" | "succeeded" | "failed";
  currentProjectStatus: "idle" | "loading" | "succeeded" | "failed";
  createStatus: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
};

export type ProjectCreatePayload = {
  name: string;
};

export type ProjectUpdatePayload = {
  name?: string;
};
