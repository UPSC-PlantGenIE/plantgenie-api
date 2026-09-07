import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { plantgenieApi } from "../api/plantgenieApi";
import { server } from "../mocks/server";
import accountReducer, { setAccountId } from "./accountSlice";
import { useAccountIdSync } from "./useAccountIdSync";

const makeWrapper = () => {
  const store = configureStore({
    reducer: {
      account: accountReducer,
      [plantgenieApi.reducerPath]: plantgenieApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(plantgenieApi.middleware),
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
  return { store, wrapper };
};

describe("useAccountIdSync", () => {
  beforeEach(() => localStorage.clear());

  it("hydrates from localStorage on mount", () => {
    localStorage.setItem("accountId", "1234567890123456");
    const { store, wrapper } = makeWrapper();
    renderHook(() => useAccountIdSync(), { wrapper });
    expect(store.getState().account.accountId).toBe("1234567890123456");
  });

  it("writes to localStorage when accountId changes", () => {
    const { store, wrapper } = makeWrapper();
    renderHook(() => useAccountIdSync(), { wrapper });
    act(() => {
      store.dispatch(setAccountId("9999888877776666"));
    });
    expect(localStorage.getItem("accountId")).toBe("9999888877776666");
  });

  it("creates an account when none is stored", async () => {
    server.use(
      http.post("http://localhost:8000/api/v2/accounts", () =>
        HttpResponse.json({ accountId: "5555444433332222" }, { status: 201 })
      )
    );
    const { store, wrapper } = makeWrapper();

    renderHook(() => useAccountIdSync(), { wrapper });

    await waitFor(() =>
      expect(store.getState().account.accountId).toBe("5555444433332222")
    );
  });
});
