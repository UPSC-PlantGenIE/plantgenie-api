import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export interface AccountState {
  accountId: string | null;
}

const initialState: AccountState = { accountId: null };

const accountSlice = createSlice({
  name: "account",
  initialState,
  reducers: {
    setAccountId(state, action: PayloadAction<string>) {
      state.accountId = action.payload;
    },
  },
});

export const { setAccountId } = accountSlice.actions;
export default accountSlice.reducer;
