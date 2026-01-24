import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import { createAsyncThunk } from "@reduxjs/toolkit";
import { ComicBuilderEndpoints } from "../../api.constants";
import type { SimpleEnvelope } from "../../types/simpleEnvelope";
import { commitStoryInput, streamStoryDeltas } from "../comicSlice";

export const streamComicStory = createAsyncThunk(
  "comicState/streamComicStory",
  async (inputText: string, { dispatch, getState }) => {
    const state = getState() as RootState;
    const projectId = state.comic.projectId;

    if (!projectId) {
      throw new Error("Project ID not found in state");
    }

    dispatch(commitStoryInput(inputText));

    const url = ComicBuilderEndpoints.phases.generateStory(projectId);
    const stream = httpClient.streamPost<SimpleEnvelope>(url, {
      storyPrompt: inputText,
    });

    for await (const envelope of stream) {
      dispatch(streamStoryDeltas(envelope));
    }
  }
);
