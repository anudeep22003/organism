const API_BASE = "/api/comic-builder";

export const ComicBuilderEndpoints = {
  projects: {
    list: () => `${API_BASE}/projects`,
    detail: (projectId: string) => `${API_BASE}/projects/${projectId}`,
  },
  phases: {
    generateStory: (projectId: string) =>
      `${API_BASE}/phase/generate-story/${projectId}`,
    extractCharacters: (projectId: string) =>
      `${API_BASE}/phase/extract-characters/${projectId}`,
    renderCharacter: (projectId: string) =>
      `${API_BASE}/phase/render-character/${projectId}`,
    generatePanels: (projectId: string) =>
      `${API_BASE}/phase/generate-panels/${projectId}`,
    renderPanel: (projectId: string) =>
      `${API_BASE}/phase/render-panel/${projectId}`,
  },
} as const;
