import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { ComicBuilderEndpoints } from "../../api.constants";
import type { Character } from "../../types/consolidatedState";
import { setCharacters } from "../comicSlice";

type ExtractCharactersResponse = {
  characters: Record<string, Character>;
};

export const extractCharacters = createAsyncThunk(
  "comicState/extractCharacters",
  async (projectId: string, { dispatch }) => {
    const response = await httpClient.get<ExtractCharactersResponse>(
      ComicBuilderEndpoints.phases.extractCharacters(projectId)
    );
    dispatch(setCharacters(response.characters));
    return response.characters;
  }
);

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
