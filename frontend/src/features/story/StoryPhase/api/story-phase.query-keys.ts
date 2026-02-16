export const storyPhaseKeys = {
  all: ["storyPhase"] as const,
  project: (projectId: string) =>
    [...storyPhaseKeys.all, "project", projectId] as const,
};
