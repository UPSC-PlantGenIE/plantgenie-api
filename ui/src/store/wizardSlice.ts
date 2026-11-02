import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface WizardState {
  name: string;
  description: string;
  taxonId: string | null;
  annotationId: string | null;
}

const initialState: WizardState = {
  name: "",
  description: "",
  taxonId: null,
  annotationId: null,
};

const wizardSlice = createSlice({
  name: "wizard",
  initialState,
  reducers: {
    setName(state, action: PayloadAction<string>) {
      state.name = action.payload;
    },
    setDescription(state, action: PayloadAction<string>) {
      state.description = action.payload;
    },
    setTaxonId(state, action: PayloadAction<string>) {
      if (state.taxonId !== action.payload) {
        state.annotationId = null;
      }
      state.taxonId = action.payload;
    },
    setAnnotationId(state, action: PayloadAction<string>) {
      state.annotationId = action.payload;
    },
    reset() {
      return initialState;
    },
  },
});

export const { setName, setDescription, setTaxonId, setAnnotationId, reset } =
  wizardSlice.actions;

export default wizardSlice.reducer;
