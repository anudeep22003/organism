import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "@/store";
import type { PhaseMapKey } from "../phaseMap";
import type { ComicState } from "../types/consolidatedState";
import type { SimpleEnvelope } from "../types/simpleEnvelope";
import { fetchComicState } from "./thunks/comicThunks";

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
    commitStoryInput: (state, action: PayloadAction<string>) => {
      if (!state) return;
      const comic = state.comic;
      if (!comic) {
        console.error(
          "Comic state not found while committing story draft"
        );
        return;
      }
      comic.state.story.userInputText.push(action.payload);
    },
    streamStory: (state, action: PayloadAction<SimpleEnvelope>) => {
      const story = state.comic?.state.story;
      if (!story) return;

      const { data } = action.payload;

      story.storyText += data.delta;
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

export const selectLastestStoryInputText = (state: RootState) => {
  const comicState = state.comic;
  if (!comicState) throw new Error("Comic state not found");
  const lastInput = comicState.comic?.state.story.userInputText.at(-1);
  return lastInput ?? "";
};

export const selectStoryText = (state: RootState) => {
  const comicState = state.comic;
  if (!comicState) {
    console.error("Comic state not found while selecting story text");
    return "";
  }
  const story = comicState.comic?.state.story;
  if (!story) {
    console.error("Story not found while selecting story text");
    return "";
  }
  return story.storyText;
};

export const {
  clearComicState,
  setCurrentPhase,
  commitStoryInput,
  streamStory,
} = comicSlice.actions;

export default comicSlice.reducer;
