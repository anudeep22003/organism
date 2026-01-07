import comicBuilderReducer from "@/pages/comic-builder/comicBuilderSlice";
import projectsReducer from "@/pages/comic-builder/projectsSlice";
import { configureStore } from "@reduxjs/toolkit";

export const store = configureStore({
  reducer: {
    comicBuilder: comicBuilderReducer,
    projects: projectsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
