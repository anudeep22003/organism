import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { ComicBuilderEndpoints } from "../../api.constants";
import type { Character } from "../../types/consolidatedState";

type RenderCharacterResponse = {
  message: string;
};

type RenderCharacterArgs = {
  projectId: string;
  character: Character;
};

export const renderCharacter = createAsyncThunk(
  "comicState/renderCharacter",
  async ({ projectId, character }: RenderCharacterArgs) => {
    const response = await httpClient.post<RenderCharacterResponse>(
      ComicBuilderEndpoints.phases.renderCharacter(projectId),
      character
    );
    // No dispatch needed - backend emits state.updated which triggers refetch
    return response;
  }
);
