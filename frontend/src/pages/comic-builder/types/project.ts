// Projects types
export type Project = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ProjectsState = {
  projects: Project[];
  status: "idle" | "loading" | "succeeded" | "failed";
  createStatus: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
};

export type ProjectCreatePayload = {
  name: string;
};

export type ProjectUpdatePayload = {
  name?: string;
};
