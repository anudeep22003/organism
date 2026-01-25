import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { ComicBuilderEndpoints } from "../../api.constants";
import type { ComicPanel } from "../../types/consolidatedState";

type GeneratePanelsResponse = {
  message: string;
};

export const generatePanels = createAsyncThunk(
  "comicState/generatePanels",
  async (projectId: string) => {
    const response = await httpClient.get<GeneratePanelsResponse>(
      ComicBuilderEndpoints.phases.generatePanels(projectId)
    );
    // No dispatch needed - backend emits state.updated which triggers refetch
    return response;
  }
);

type RenderPanelResponse = {
  message: string;
};

type RenderPanelArgs = {
  projectId: string;
  panel: ComicPanel;
};

export const renderPanel = createAsyncThunk(
  "comicState/renderPanel",
  async ({ projectId, panel }: RenderPanelArgs) => {
    const response = await httpClient.post<RenderPanelResponse>(
      ComicBuilderEndpoints.phases.renderPanel(projectId),
      panel
    );
    // No dispatch needed - backend emits state.updated which triggers refetch
    return response;
  }
);
