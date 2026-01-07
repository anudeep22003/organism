import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import type { Project, ProjectsState } from "./types";

const initialState: ProjectsState = {
  projects: [],
  status: "idle",
  error: null,
};

export const fetchProjects = createAsyncThunk(
  "projects/fetchProjects",
  async () => {
    const projects = await httpClient.get<Project[]>(
      "/api/comic-builder/projects"
    );
    return projects;
  }
);

export const projectsSlice = createSlice({
  name: "projects",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchProjects.pending, (state) => {
      state.status = "loading";
      state.error = null;
    });
    builder.addCase(fetchProjects.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.projects = action.payload;
    });
    builder.addCase(fetchProjects.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message ?? "Failed to fetch projects";
    });
  },
});

const selectProjects = (state: RootState) => state.projects.projects;
const selectProjectsStatus = (state: RootState) =>
  state.projects.status;
const selectProjectsError = (state: RootState) => state.projects.error;

export { selectProjects, selectProjectsError, selectProjectsStatus };

export default projectsSlice.reducer;
