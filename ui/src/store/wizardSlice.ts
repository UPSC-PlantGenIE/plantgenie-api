import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export type WizardStep = 1 | 2 | 3

export interface WizardState {
  step: WizardStep
  name: string
  description: string
  taxonId: string | null
  genomeId: string | null
}

const initialState: WizardState = {
  step: 1,
  name: '',
  description: '',
  taxonId: null,
  genomeId: null,
}

const wizardSlice = createSlice({
  name: 'wizard',
  initialState,
  reducers: {
    next(state) {
      if (state.step < 3) {
        state.step = (state.step + 1) as WizardStep
      }
    },
    back(state) {
      if (state.step > 1) {
        state.step = (state.step - 1) as WizardStep
      }
    },
    setName(state, action: PayloadAction<string>) {
      state.name = action.payload
    },
    setDescription(state, action: PayloadAction<string>) {
      state.description = action.payload
    },
    setTaxonId(state, action: PayloadAction<string>) {
      if (state.taxonId !== action.payload) {
        state.genomeId = null
      }
      state.taxonId = action.payload
    },
    setGenomeId(state, action: PayloadAction<string>) {
      state.genomeId = action.payload
    },
  },
})

export const { next, back, setName, setDescription, setTaxonId, setGenomeId } =
  wizardSlice.actions

export default wizardSlice.reducer
