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
