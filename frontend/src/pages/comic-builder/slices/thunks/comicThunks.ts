import { httpClient } from "@/lib/httpClient";
import { createAsyncThunk } from "@reduxjs/toolkit";
import type { Comic } from "../../types/consolidatedState";

export const fetchComicState = createAsyncThunk(
  "comicState/fetchComicState",
  async (projectId: string) => {
    const comic = await httpClient.get<Comic>(
      `/api/comic-builder/projects/${projectId}`
    );
    return comic;
  }
);