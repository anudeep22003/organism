import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { ComicBuilderEndpoints } from "../api.constants";

import type {
  Project,
  ProjectCreatePayload,
  ProjectsState,
  ProjectUpdatePayload,
} from "../types/project";

const initialState: ProjectsState = {
  projects: [],
  status: "idle",
  createStatus: "idle",
  error: null,
};

export const fetchProjects = createAsyncThunk(
  "projects/fetchProjects",
  async () => {
    const projects = await httpClient.get<Project[]>(
      ComicBuilderEndpoints.projects.list()
    );
    return projects;
  }
);

export const fetchProject = createAsyncThunk(
  "projects/fetchProject",
  async (projectId: string) => {
    const project = await httpClient.get<Project>(
      ComicBuilderEndpoints.projects.detail(projectId)
    );
    return project;
  }
);

export const createProject = createAsyncThunk(
  "projects/createProject",
  async (payload: ProjectCreatePayload) => {
    const project = await httpClient.post<Project>(
      ComicBuilderEndpoints.projects.list(),
      payload
    );
    return project;
  }
);

export const updateProject = createAsyncThunk(
  "projects/updateProject",
  async ({
    id,
    payload,
  }: {
    id: string;
    payload: ProjectUpdatePayload;
  }) => {
    const project = await httpClient.patch<Project>(
      ComicBuilderEndpoints.projects.detail(id),
      payload
    );
    return project;
  }
);

export const deleteProject = createAsyncThunk(
  "projects/deleteProject",
  async (id: string) => {
    await httpClient.delete(ComicBuilderEndpoints.projects.detail(id));
    return id;
  }
);

export const projectsSlice = createSlice({
  name: "projects",
  initialState,
  reducers: {
    resetCreateStatus: (state) => {
      state.createStatus = "idle";
    },
  },
  extraReducers: (builder) => {
    // Fetch projects
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

    // Create project
    builder.addCase(createProject.pending, (state) => {
      state.createStatus = "loading";
      state.error = null;
    });
    builder.addCase(createProject.fulfilled, (state, action) => {
      state.createStatus = "succeeded";
      state.projects.push(action.payload);
    });
    builder.addCase(createProject.rejected, (state, action) => {
      state.createStatus = "failed";
      state.error = action.error.message ?? "Failed to create project";
    });

    // Update project
    builder.addCase(updateProject.fulfilled, (state, action) => {
      const index = state.projects.findIndex(
        (p) => p.id === action.payload.id
      );
      if (index !== -1) {
        state.projects[index] = action.payload;
      }
    });

    // Delete project
    builder.addCase(deleteProject.fulfilled, (state, action) => {
      state.projects = state.projects.filter(
        (p) => p.id !== action.payload
      );
    });
  },
});

export const { resetCreateStatus } = projectsSlice.actions;

const selectProjects = (state: RootState) => state.projects.projects;
const selectProjectsStatus = (state: RootState) =>
  state.projects.status;
const selectProjectsError = (state: RootState) => state.projects.error;
const selectCreateStatus = (state: RootState) =>
  state.projects.createStatus;

export {
  selectCreateStatus,
  selectProjects,
  selectProjectsError,
  selectProjectsStatus,
};

export default projectsSlice.reducer;
