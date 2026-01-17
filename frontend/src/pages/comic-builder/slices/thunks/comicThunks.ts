import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import { createAsyncThunk } from "@reduxjs/toolkit";
import type {
  Character,
  ComicPanel,
  ConsolidatedComicState,
  Story,
} from "../../types/consolidatedState";
import { selectSyncPayload } from "../comicSlice";

/**
 * Response shape from backend API.
 * Backend returns Project + nested state.
 */
type ComicProjectApiResponse = {
  id: string;
  name: string | null;
  createdAt: string;
  updatedAt: string;
  state: ConsolidatedComicState;
};

/**
 * Flattened shape expected by the slice.
 */
export type ComicProjectPayload = {
  projectId: string;
  projectName: string | null;
  createdAt: string;
  updatedAt: string;
  story: Story;
  characters: Record<string, Character>;
  panels: ComicPanel[];
};

/**
 * Fetch comic project and flatten the response for the slice.
 */
export const fetchComicState = createAsyncThunk(
  "comicState/fetchComicState",
  async (projectId: string): Promise<ComicProjectPayload> => {
    const response = await httpClient.get<ComicProjectApiResponse>(
      `/api/comic-builder/projects/${projectId}`
    );

    // Transform nested response to flat slice payload
    return {
      projectId: response.id,
      projectName: response.name,
      createdAt: response.createdAt,
      updatedAt: response.updatedAt,
      story: response.state.story,
      characters: response.state.characters,
      panels: response.state.panels,
    };
  }
);

export const syncComicState = createAsyncThunk(
  "comicState/syncComicState",
  async (_, { getState }) => {
    const state = getState() as RootState;
    const comicState = state.comic;
    if (!comicState) {
      throw new Error("Comic state not found");
    }
    const payload = {
      state: selectSyncPayload(state),
    };
    const response = await httpClient.patch<ComicProjectApiResponse>(
      `/api/comic-builder/projects/${comicState.projectId}`,
      payload
    );
    return response;
  }
);
