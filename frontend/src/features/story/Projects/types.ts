export type ProjectListEntryType = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  storyCount: number;
};

export type ProjectHomeType = ProjectListEntryType & {
  stories?: Record<string, unknown>;
  characters?: Record<string, unknown>;
  panels?: Record<string, unknown>;
};
