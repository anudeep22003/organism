import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import type { SimpleEnvelope } from "../../types/simpleEnvelope";
import { commitStoryInput, streamStory } from "../comicSlice";

export const streamComicStory = createAsyncThunk(
  "comicState/streamComicStory",
  async (inputText: string, { dispatch }) => {
    dispatch(commitStoryInput(inputText));

    const stream = httpClient.streamPost<SimpleEnvelope>({
      storyPrompt: inputText,
    });

    for await (const envelope of stream) {
      dispatch(streamStory(envelope));
    }
  }
);
