import { httpClient } from "@/lib/httpClient";
import type { PayloadAction } from "@reduxjs/toolkit";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

type Story = {
  id: string;
  text: string;
  status: "idle" | "streaming" | "complete";
};

type ComicBuilderState = {
  inputText: string;
  story?: Story;
};

const initialState: ComicBuilderState = {
  inputText: "",
};

// simple envelope that the backend sends
type SimpleEnvelope = {
  id: string;
  ts: number;

  requestId?: string;
  streamId?: string;
  seq?: number;

  data: { delta?: string; finish_reason?: string };
};

export const streamComicStory = createAsyncThunk(
  "comicBuilder/streamComicStory",
  async (_, { dispatch }) => {
    const stream = httpClient.streamPost<SimpleEnvelope>();

    for await (const envelope of stream) {
      if (envelope.data.finish_reason === "stop") {
        dispatch(markStoryComplete());
        break;
      }
      dispatch(addToStoryText(envelope));
    }
  }
);

export const comicBuilderSlice = createSlice({
  name: "comicBuilder",
  initialState,
  reducers: {
    setInputText: (state, action: PayloadAction<string>) => {
      state.inputText = action.payload;
    },
    addToStoryText: (state, action: PayloadAction<SimpleEnvelope>) => {
      const { data, id } = action.payload;

      if (data.delta === "start") {
        state.story = { id, text: "", status: "streaming" };
      }
      if (state.story?.status === "streaming" && data.delta) {
        state.story.text += ` ${data.delta}`;
      }
    },
    markStoryComplete: (state) => {
      if (state.story) {
        state.story.status = "complete";
      }
    },
  },
  extraReducers: (builder) => {
    builder.addCase(streamComicStory.pending, (state) => {
      state.story = { id: "", text: "", status: "streaming" };
    });
    builder.addCase(streamComicStory.rejected, (state, action) => {
      if (state.story) {
        state.story.status = "idle";
      }
      console.error("Error streaming comic story:", action.error);
    });
  },
});

export const { setInputText, addToStoryText, markStoryComplete } =
  comicBuilderSlice.actions;

export default comicBuilderSlice.reducer;
