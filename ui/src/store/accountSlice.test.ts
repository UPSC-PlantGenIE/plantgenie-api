import { describe, it, expect } from "vitest";
import reducer, { clearAccountId, setAccountId } from "./accountSlice";

describe("accountSlice", () => {
  it("starts with null accountId", () => {
    expect(reducer(undefined, { type: "@@INIT" })).toEqual({ accountId: null });
  });

  it("starts with a accountId from local storage", () => {
    localStorage.setItem("accountId", "1234567890123456");
    expect(reducer(undefined, { type: "@@INIT" }).accountId).toBe(
      "1234567890123456"
    );
  });

  it("setAccountId stores the id", () => {
    const next = reducer({ accountId: null }, setAccountId("1234567890123456"));
    expect(next.accountId).toBe("1234567890123456");
  });

  it("clearAccountId stores null as id", () => {
    // clearAccountId()
    const next = reducer({ accountId: "1234567890123456" }, clearAccountId());
    expect(next.accountId).toBeNull();
  });
});
