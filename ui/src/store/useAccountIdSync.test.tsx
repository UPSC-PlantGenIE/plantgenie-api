import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import type { ReactNode } from "react";
import accountReducer, { setAccountId } from "./accountSlice";
import { useAccountIdSync } from "./useAccountIdSync";

const makeWrapper = () => {
  const store = configureStore({ reducer: { account: accountReducer } });
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
});
