import { describe, it, expect } from "vitest";
import reducer, { setAccountId } from "./accountSlice";

describe("accountSlice", () => {
  it("starts with null accountId", () => {
    expect(reducer(undefined, { type: "@@INIT" })).toEqual({ accountId: null });
  });

  it("setAccountId stores the id", () => {
    const next = reducer({ accountId: null }, setAccountId("1234567890123456"));
    expect(next.accountId).toBe("1234567890123456");
  });
});
