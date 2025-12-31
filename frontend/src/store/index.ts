import { configureStore } from "@reduxjs/toolkit";
import comicBuilderReducer from "@/pages/comic-builder/comicBuilderSlice";

export const store = configureStore({
  reducer: {
    comicBuilder: comicBuilderReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
