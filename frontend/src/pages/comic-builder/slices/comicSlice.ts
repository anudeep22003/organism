import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import type { Comic, ComicState } from "../types/consolidatedState";
import type { RootState } from "@/store";

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

export const { clearComicState } = comicSlice.actions;

export default comicSlice.reducer;
