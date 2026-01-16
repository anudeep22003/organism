import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import type { Character } from "../../types/consolidatedState";
import { setCharacters } from "../comicSlice";

type ExtractCharactersResponse = {
  characters: Record<string, Character>;
};

export const extractCharacters = createAsyncThunk(
  "comicState/extractCharacters",
  async (projectId: string, { dispatch }) => {
    const response = await httpClient.get<ExtractCharactersResponse>(
      `/api/comic-builder/phase/extract-characters/${projectId}`
    );
    dispatch(setCharacters(response.characters));
    return response.characters;
  }
);

