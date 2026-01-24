import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";

type GeneratePanelsResponse = {
  message: string;
};

export const generatePanels = createAsyncThunk(
  "comicState/generatePanels",
  async (projectId: string) => {
    const response = await httpClient.get<GeneratePanelsResponse>(
      `/api/comic-builder/phase/generate-panels/${projectId}`
    );
    // No dispatch needed - backend emits state.updated which triggers refetch
    return response;
  }
);
