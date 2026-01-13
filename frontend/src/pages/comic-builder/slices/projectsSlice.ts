import { httpClient } from "@/lib/httpClient";
import type { RootState } from "@/store";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import type {
  Project,
  ProjectCreatePayload,
  ProjectsState,
  ProjectUpdatePayload,
} from "../types/project";

const initialState: ProjectsState = {
  projects: [],
  currentProject: null,
  status: "idle",
  currentProjectStatus: "idle",
  createStatus: "idle",
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

export const fetchProject = createAsyncThunk(
  "projects/fetchProject",
  async (projectId: string) => {
    const project = await httpClient.get<Project>(
      `/api/comic-builder/projects/${projectId}`
    );
    return project;
  }
);

export const createProject = createAsyncThunk(
  "projects/createProject",
  async (payload: ProjectCreatePayload) => {
    const project = await httpClient.post<Project>(
      "/api/comic-builder/projects",
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
      `/api/comic-builder/projects/${id}`,
      payload
    );
    return project;
  }
);

export const deleteProject = createAsyncThunk(
  "projects/deleteProject",
  async (id: string) => {
    await httpClient.delete(`/api/comic-builder/projects/${id}`);
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
    clearCurrentProject: (state) => {
      state.currentProject = null;
      state.currentProjectStatus = "idle";
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

    // Fetch single project
    builder.addCase(fetchProject.pending, (state) => {
      state.currentProjectStatus = "loading";
      state.error = null;
    });
    builder.addCase(fetchProject.fulfilled, (state, action) => {
      state.currentProjectStatus = "succeeded";
      state.currentProject = action.payload;
    });
    builder.addCase(fetchProject.rejected, (state, action) => {
      state.currentProjectStatus = "failed";
      state.error = action.error.message ?? "Failed to fetch project";
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

export const { resetCreateStatus, clearCurrentProject } =
  projectsSlice.actions;

const selectProjects = (state: RootState) => state.projects.projects;
const selectProjectsStatus = (state: RootState) =>
  state.projects.status;
const selectProjectsError = (state: RootState) => state.projects.error;
const selectCreateStatus = (state: RootState) =>
  state.projects.createStatus;
const selectCurrentProject = (state: RootState) =>
  state.projects.currentProject;
const selectCurrentProjectStatus = (state: RootState) =>
  state.projects.currentProjectStatus;

export {
  selectCreateStatus,
  selectCurrentProject,
  selectCurrentProjectStatus,
  selectProjects,
  selectProjectsError,
  selectProjectsStatus,
};

export default projectsSlice.reducer;
