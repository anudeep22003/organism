import { httpClient } from "@/lib/httpClient";
import {
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from "@reduxjs/toolkit";

import type { PhaseMapKey } from "../phaseMap";
import type { Comic, ComicState } from "../types/consolidatedState";

export const fetchComicState = createAsyncThunk(
  "comic/fetchComicState",
  async (projectId: string) => {
    const comic = await httpClient.get<Comic>(
      `/api/comic-builder/projects/${projectId}`
    );
    return comic;
  }
);

const initialState: ComicState = {
  comic: null,
  currentPhase: "write-story",
  status: "idle",
  error: null,
};

export const comicSlice = createSlice({
  name: "comicState",
  initialState,
  reducers: {
    clearComicState: (state) => {
      state.comic = null;
      state.status = "idle";
      state.error = null;
    },
    setCurrentPhase: (state, action: PayloadAction<PhaseMapKey>) => {
      state.currentPhase = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch comic project
    builder.addCase(fetchComicState.pending, (state) => {
      state.status = "loading";
      state.error = null;
    });
    builder.addCase(fetchComicState.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.comic = action.payload;
    });
    builder.addCase(fetchComicState.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message ?? "Failed to fetch project";
    });
  },
});

export const { clearComicState, setCurrentPhase } = comicSlice.actions;

export default comicSlice.reducer;
