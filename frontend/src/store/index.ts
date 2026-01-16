import comicReducer from "@/pages/comic-builder/slices/comicSlice";
import projectsReducer from "@/pages/comic-builder/slices/projectsSlice";
import { configureStore } from "@reduxjs/toolkit";

export const store = configureStore({
  reducer: {
    comic: comicReducer,
    projects: projectsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
