import type { PropsWithChildren, ReactElement } from 'react'
import { render, type RenderOptions } from '@testing-library/react'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import { plantgenieApi } from './api/plantgenieApi'
import wizardReducer from './store/wizardSlice'
import type { RootState } from './store'

function makeStore(preloadedState?: Partial<RootState>) {
  return configureStore({
    reducer: {
      wizard: wizardReducer,
      [plantgenieApi.reducerPath]: plantgenieApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(plantgenieApi.middleware),
    preloadedState: preloadedState as RootState | undefined,
  })
}

export type AppStore = ReturnType<typeof makeStore>

interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: Partial<RootState>
  store?: AppStore
}

export function renderWithStore(
  ui: ReactElement,
  {
    preloadedState,
    store = makeStore(preloadedState),
    ...renderOptions
  }: ExtendedRenderOptions = {},
) {
  function Wrapper({ children }: PropsWithChildren) {
    return <Provider store={store}>{children}</Provider>
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) }
}
