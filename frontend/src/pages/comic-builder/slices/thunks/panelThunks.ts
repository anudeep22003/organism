import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { ComicBuilderEndpoints } from "../../api.constants";

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
