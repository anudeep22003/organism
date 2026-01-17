import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "@/store";
import type { PhaseMapKey } from "../phaseMap";
import type { Character, ComicState } from "../types/consolidatedState";
import type { SimpleEnvelope } from "../types/simpleEnvelope";
import { fetchComicState } from "./thunks/comicThunks";

const initialState: ComicState = {
  // Project metadata
  projectId: null,
  projectName: null,
  createdAt: null,
  updatedAt: null,

  // Phase
  currentPhase: "write-story",

  // Domain data (flat)
  story: null,
  characters: {},
  panels: [],

  // Fetch status
  fetchStatus: "idle",
  error: null,
};

export const comicSlice = createSlice({
  name: "comicState",
  initialState,
  reducers: {
    clearComicState: (state) => {
      state.projectId = null;
      state.projectName = null;
      state.createdAt = null;
      state.updatedAt = null;
      state.story = null;
      state.characters = {};
      state.panels = [];
      state.fetchStatus = "idle";
      state.error = null;
    },

    setCurrentPhase: (state, action: PayloadAction<PhaseMapKey>) => {
      state.currentPhase = action.payload;
    },

    commitStoryInput: (state, action: PayloadAction<string>) => {
      if (!state.story) {
        console.error("Story not found while committing story draft");
        return;
      }
      state.story.userInputText.push(action.payload);
    },

    streamStoryDeltas: (
      state,
      action: PayloadAction<SimpleEnvelope>
    ) => {
      if (!state.story) return;

      const { data } = action.payload;

      if (data.delta === "") {
        // Start of stream - set status
        state.story.status = "streaming";
        return;
      }

      if (data.delta) {
        state.story.storyText += data.delta;
      }

      if (data.finish_reason === "stop") {
        state.story.status = "completed";
        console.log("Story streaming completed");
      }
    },

    setCharacters: (
      state,
      action: PayloadAction<Record<string, Character>>
    ) => {
      state.characters = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchComicState.pending, (state) => {
      state.fetchStatus = "loading";
      state.error = null;
    });
    builder.addCase(fetchComicState.fulfilled, (state, action) => {
      state.fetchStatus = "succeeded";
      // Destructure the response into flat state
      const {
        projectId,
        projectName,
        createdAt,
        updatedAt,
        story,
        characters,
        panels,
      } = action.payload;
      state.projectId = projectId;
      state.projectName = projectName;
      state.createdAt = createdAt;
      state.updatedAt = updatedAt;
      state.story = story;
      state.characters = characters;
      state.panels = panels;
    });
    builder.addCase(fetchComicState.rejected, (state, action) => {
      state.fetchStatus = "failed";
      state.error = action.error.message ?? "Failed to fetch project";
    });
  },
});

// === Selectors ===

export const selectStory = (state: RootState) => state.comic.story;

export const selectStoryText = (state: RootState) =>
  state.comic.story?.storyText ?? "";

export const selectStoryStatus = (state: RootState) =>
  state.comic.story?.status ?? "idle";

export const selectLatestStoryInputText = (state: RootState) =>
  state.comic.story?.userInputText.at(-1) ?? "";

export const selectCharacters = (
  state: RootState
): Record<string, Character> => state.comic.characters;

export const selectCharacterById = (
  state: RootState,
  characterId: string
) => state.comic.characters[characterId] ?? null;

export const selectSyncPayload = (state: RootState) => {
  return {
    story: state.comic.story,
    characters: state.comic.characters,
    panels: state.comic.panels,
  };
};

export const selectPanels = (state: RootState) => state.comic.panels;

export const selectFetchStatus = (state: RootState) =>
  state.comic.fetchStatus;

export const {
  clearComicState,
  setCurrentPhase,
  commitStoryInput,
  streamStoryDeltas,
  setCharacters,
} = comicSlice.actions;

export default comicSlice.reducer;
