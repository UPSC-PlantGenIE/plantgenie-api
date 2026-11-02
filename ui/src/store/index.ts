import { configureStore } from "@reduxjs/toolkit";
import { plantgenieApi } from "../api/plantgenieApi";
import accountReducer from "./accountSlice";

export const store = configureStore({
  reducer: {
    account: accountReducer,
    [plantgenieApi.reducerPath]: plantgenieApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(plantgenieApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
