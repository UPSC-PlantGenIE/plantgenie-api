import type { PropsWithChildren, ReactElement } from "react";
import { Provider } from "react-redux";
import { render, type RenderOptions } from "@testing-library/react";
import { configureStore } from "@reduxjs/toolkit";
import { plantgenieApi } from "./api/plantgenieApi";
import type { RootState } from "./store";
import wizardReducer from "./store/wizardSlice";
import accountReducer from "./store/accountSlice";

function makeStore(preloadedState?: Partial<RootState>) {
  return configureStore({
    reducer: {
      account: accountReducer,
      wizard: wizardReducer,
      [plantgenieApi.reducerPath]: plantgenieApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(plantgenieApi.middleware),
    preloadedState: preloadedState as RootState | undefined,
  });
}

export type AppStore = ReturnType<typeof makeStore>;

interface ExtendedRenderOptions extends Omit<RenderOptions, "queries"> {
  preloadedState?: Partial<RootState>;
  store?: AppStore;
}

export function renderWithStore(
  ui: ReactElement,
  {
    preloadedState,
    store = makeStore(preloadedState),
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: PropsWithChildren) {
    return <Provider store={store}>{children}</Provider>;
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}
