import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import {
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from "@reduxjs/toolkit";

import type { ComicPhase, ComicState, SimpleEnvelope } from "./types";

// State is null until a project is loaded from the backend
const initialState: ComicState | null = null;

export const streamComicStory = createAsyncThunk(
  "comicBuilder/streamComicStory",
  async (inputText: string, { dispatch }) => {
    const stream = httpClient.streamPost<SimpleEnvelope>({
      storyPrompt: inputText,
    });

    for await (const envelope of stream) {
      dispatch(addToCurrentPhaseContent(envelope));
    }

    // Sync project state after streaming is complete
    dispatch(syncProjectState());
  }
);

export const extractCharacters = createAsyncThunk(
  "comicBuilder/extractCharacters",
  async (projectId: string, { dispatch }) => {
    const response = await httpClient.get<ComicState>(
      `/api/comic-builder/phase/extract-characters/${projectId}`
    );
    if (response) {
      dispatch(loadProjectState(response));
    }
    return response;
  }
);

export const syncProjectState = createAsyncThunk(
  "comicBuilder/syncProjectState",
  async (_, { getState }) => {
    const state = getState() as RootState;
    const projectId = state.projects.currentProject?.id;
    const comicState = state.comicBuilder;

    if (!projectId || !comicState) return;

    await httpClient.patch(`/api/comic-builder/projects/${projectId}`, {
      state: comicState,
    });
  }
);

export const comicBuilderSlice = createSlice({
  name: "comicBuilder",
  initialState: initialState as ComicState | null,
  reducers: {
    loadProjectState: (_state, action: PayloadAction<ComicState>) => {
      return action.payload;
    },
    clearProjectState: () => {
      return null;
    },
    addPhase: (state) => {
      if (!state) return;
      const newPhase: ComicPhase = {
        id: crypto.randomUUID(),
        name: "Phase " + (state.phases.length + 1),
        inputText: "",
        content: null,
      };
      state.phases.push(newPhase);
      state.currentPhaseIndex = state.phases.length - 1;
    },
    setCurrentPhaseIndex: (state, action: PayloadAction<number>) => {
      if (!state) return;
      if (action.payload >= 0 && action.payload < state.phases.length) {
        state.currentPhaseIndex = action.payload;
      } else {
        console.error("Invalid phase index", action.payload);
      }
    },
    goToSpecificPhase: (state, action: PayloadAction<number>) => {
      if (!state) return;
      const maxIndex = state.phases.length - 1;
      if (action.payload >= 0 && action.payload <= maxIndex) {
        state.currentPhaseIndex = action.payload;
      } else {
        console.error(
          "Invalid phase index, max index is",
          maxIndex,
          "and you tried to go to",
          action.payload
        );
      }
    },
    setInputText: (state, action: PayloadAction<string>) => {
      if (!state) return;
      state.phases[state.currentPhaseIndex].inputText = action.payload;
    },
    addToCurrentPhaseContent: (
      state,
      action: PayloadAction<SimpleEnvelope>
    ) => {
      if (!state) return;
      const { data } = action.payload;
      const currentPhase = state.phases[state.currentPhaseIndex];

      // if past the start phase, content should exist otherwise throw Error
      if (!currentPhase.content) {
        console.error("No content object");
        throw new Error("No content object");
      }

      // if start delta then initialize a content object and set to idle
      if (data.delta === "") {
        currentPhase.content.status = "streaming";
        return;
      }
      // if streaming delta then add to the text field and set to streaming
      if (data.delta) {
        currentPhase.content.text += data.delta;
      }
      // if finish_reason then mark as completed
      if (data.finish_reason === "stop") {
        currentPhase.content.status = "completed";
      }
    },
  },
  extraReducers: (builder) => {
    builder.addCase(streamComicStory.rejected, (state, action) => {
      if (!state) return;
      const currentPhase = state.phases[state.currentPhaseIndex];
      const currentContent = currentPhase.content;

      if (!currentContent) {
        console.error("No content object");
        return;
      }

      currentContent.status = "error";
      console.error("Error streaming comic story:", action.error);
    });
  },
});

const selectComicBuilderState = (state: RootState) =>
  state.comicBuilder;

const selectCurrentPhaseInputText = (state: RootState) => {
  const comicState = state.comicBuilder;
  if (!comicState) return "";
  return comicState.phases[comicState.currentPhaseIndex].inputText;
};

const selectCurrentPhaseContent = (state: RootState) => {
  const comicState = state.comicBuilder;
  if (!comicState) return null;
  return comicState.phases[comicState.currentPhaseIndex].content;
};

const selectCurrentPhaseIndex = (state: RootState) => {
  const comicState = state.comicBuilder;
  if (!comicState) return 0;
  return comicState.currentPhaseIndex;
};

const selectCurrentPhase = (state: RootState) => {
  const comicState = state.comicBuilder;
  if (!comicState) return null;
  return comicState.phases[comicState.currentPhaseIndex];
};

const selectCurrentPhaseName = (state: RootState) => {
  const currentPhase = selectCurrentPhase(state);
  if (!currentPhase) return null;
  return currentPhase.name;
};

const selectPhases = (state: RootState) => {
  const comicState = state.comicBuilder;
  if (!comicState) return [];
  return comicState.phases;
};

export const {
  loadProjectState,
  clearProjectState,
  addPhase,
  setCurrentPhaseIndex,
  setInputText,
  addToCurrentPhaseContent,
  goToSpecificPhase,
} = comicBuilderSlice.actions;

export {
  selectComicBuilderState,
  selectCurrentPhase,
  selectCurrentPhaseContent,
  selectCurrentPhaseIndex,
  selectCurrentPhaseInputText,
  selectCurrentPhaseName,
  selectPhases,
};

export default comicBuilderSlice.reducer;
