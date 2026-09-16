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

  it("hydrates from localStorage on mount", async () => {
    localStorage.setItem("accountId", "1234567890123456");
    const { store, wrapper } = makeWrapper();
    renderHook(() => useAccountIdSync(), { wrapper });
    await waitFor(() =>
      expect(store.getState().account.accountId).toBe("1234567890123456")
    );
  });

  it("does not use a stored id the backend rejects", async () => {
    let authorization: string | null = null;
    server.use(
      http.get("http://localhost:8000/api/v2/accounts/me", ({ request }) => {
        authorization = request.headers.get("Authorization");
        return HttpResponse.json(
          { detail: "Unknown account" },
          { status: 401 }
        );
      })
    );
    localStorage.setItem("accountId", "1234567890123456");
    const { store, wrapper } = makeWrapper();

    renderHook(() => useAccountIdSync(), { wrapper });

    await waitFor(() =>
      expect(authorization).toBe("Bearer 1234567890123456")
    );
    expect(store.getState().account.accountId).toBeNull();
  });

  it("writes to localStorage when accountId changes", () => {
    const { store, wrapper } = makeWrapper();
    renderHook(() => useAccountIdSync(), { wrapper });
    act(() => {
      store.dispatch(setAccountId("9999888877776666"));
    });
    expect(localStorage.getItem("accountId")).toBe("9999888877776666");
  });
});
