import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

interface ComicBuilderState {
  inputText: string;
}

const initialState: ComicBuilderState = {
  inputText: "",
};

export const comicBuilderSlice = createSlice({
  name: "comicBuilder",
  initialState,
  reducers: {
    setInputText: (state, action: PayloadAction<string>) => {
      state.inputText = action.payload;
    },
  },
});

export const { setInputText } = comicBuilderSlice.actions;

export default comicBuilderSlice.reducer;
