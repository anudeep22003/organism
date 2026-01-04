import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import {
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from "@reduxjs/toolkit";

import type { ComicBuilderState, Phase, SimpleEnvelope } from "./types";

/**
 So we need to add phases in
 we can have a current phase object, 
 and then a list of phases that we can keep adding to
 each phase can have its own shape for now
 but with a list we need to keep track of what the user is viewing right now. 
 this will allow you to go back and forward and see the past
 within each phase you are interacting in multiple back and forths with the AI,
 this also has the added advantage of allowing you to make changes and to regenerate. 
 but then will each phase have its own input text? 
 Yes because if you go back you should be able to see what you typed last, nice user experience. 
 we should probably have a commit object inside each phase which marks what the user likes the best, 
 and what gets shared in the future, this could be what is taken as envirnoment context for the agents.

 we have to think about how this state on the frontend translates to saved user state in the backend. 
 */

const initialPhase: Phase = {
  id: crypto.randomUUID(),
  name: "Phase 1",
  inputText: "",
  content: undefined,
};

const initialState: ComicBuilderState = {
  phases: [
    { ...initialPhase },
    { ...initialPhase },
    { ...initialPhase },
  ],
  currentPhaseIndex: 2,
};

export const streamComicStory = createAsyncThunk(
  "comicBuilder/streamComicStory",
  async (inputText: string, { dispatch }) => {
    const stream = httpClient.streamPost<SimpleEnvelope>({
      storyPrompt: inputText,
    });

    for await (const envelope of stream) {
      dispatch(addToCurrentPhaseContent(envelope));
    }
  }
);

export const comicBuilderSlice = createSlice({
  name: "comicBuilder",
  initialState,
  reducers: {
    addPhase: (state) => {
      // add new phase, set currentPhaseIndex to new phase
      const newPhase = {
        id: crypto.randomUUID(),
        name: "Phase " + (state.phases.length + 1),
        inputText: "",
      };
      state.phases.push(newPhase);
      state.currentPhaseIndex = state.phases.length - 1;
    },
    setCurrentPhaseIndex: (state, action: PayloadAction<number>) => {
      // if the phase index is valid, set the current phase index
      if (action.payload >= 0 && action.payload < state.phases.length) {
        state.currentPhaseIndex = action.payload;
      } else {
        console.error("Invalid phase index", action.payload);
      }
    },
    goToSpecificPhase: (state, action: PayloadAction<number>) => {
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
      state.phases[state.currentPhaseIndex].inputText = action.payload;
    },
    addToCurrentPhaseContent: (
      state,
      action: PayloadAction<SimpleEnvelope>
    ) => {
      const { data, id } = action.payload;
      const currentPhase = state.phases[state.currentPhaseIndex];

      // if start delta then initialize a content object and set to idle
      if (data.delta === "start") {
        currentPhase.content = {
          id,
          text: "",
          type: "text",
          status: "idle",
        };
        return; // no need to add to content text if start
      }
      // if past the start phase, content should exist otherwise throw Error
      if (!currentPhase.content) {
        console.error("No content object");
        throw new Error("No content object");
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
    builder.addCase(streamComicStory.pending, (state) => {
      // if current phase index is null then this is an error state
      state.phases[state.currentPhaseIndex].content = {
        id: "",
        text: "",
        type: "text",
        status: "streaming",
      };
    });
    builder.addCase(streamComicStory.rejected, (state, action) => {
      const currentPhase = state.phases[state.currentPhaseIndex];
      const currentContent = currentPhase.content;

      if (!currentContent) {
        console.error("No content object");
        return; // no need to set content to error if no content object
      }

      // set content to error
      currentContent.status = "error";
      console.error("Error streaming comic story:", action.error);
    });
  },
});

const selectCurrentPhaseInputText = (state: RootState) => {
  return state.comicBuilder.phases[state.comicBuilder.currentPhaseIndex]
    .inputText;
};

const selectCurrentPhaseContent = (state: RootState) => {
  return state.comicBuilder.phases[state.comicBuilder.currentPhaseIndex]
    .content;
};

export const {
  addPhase,
  setCurrentPhaseIndex,
  setInputText,
  addToCurrentPhaseContent,
  goToSpecificPhase,
} = comicBuilderSlice.actions;

export { selectCurrentPhaseContent, selectCurrentPhaseInputText };

export default comicBuilderSlice.reducer;
