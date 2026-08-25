import { describe, it, expect } from "vitest";
import reducer, {
  back,
  next,
  setAnnotationId,
  setTaxonId,
  type WizardState,
} from "./wizardSlice";

const baseState: WizardState = {
  step: 1,
  name: "",
  description: "",
  taxonId: null,
  annotationId: null,
};

describe("wizardSlice", () => {
  it("advances step with next()", () => {
    const s1 = reducer(baseState, next());
    expect(s1.step).toBe(2);
    const s2 = reducer(s1, next());
    expect(s2.step).toBe(3);
  });

  it("clamps next() at step 3", () => {
    const atEnd = { ...baseState, step: 3 as const };
    expect(reducer(atEnd, next()).step).toBe(3);
  });

  it("clamps back() at step 1", () => {
    expect(reducer(baseState, back()).step).toBe(1);
  });

  it("clears annotationId when taxon changes", () => {
    const state = {
      ...baseState,
      taxonId: "pinus-sylvestris",
      annotationId: "pinus-sylvestris-v2",
    };
    const next = reducer(state, setTaxonId("picea-abies"));
    expect(next.taxonId).toBe("picea-abies");
    expect(next.annotationId).toBeNull();
  });

  it("keeps annotationId when taxon is re-selected to the same value", () => {
    const state = {
      ...baseState,
      taxonId: "pinus-sylvestris",
      annotationId: "pinus-sylvestris-v2",
    };
    const next = reducer(state, setTaxonId("pinus-sylvestris"));
    expect(next.taxonId).toBe("pinus-sylvestris");
    expect(next.annotationId).toBe("pinus-sylvestris-v2");
  });

  it("setAnnotationId updates annotationId only", () => {
    const state = { ...baseState, taxonId: "pinus-sylvestris" };
    const next = reducer(state, setAnnotationId("pinus-sylvestris-v2"));
    expect(next.annotationId).toBe("pinus-sylvestris-v2");
    expect(next.taxonId).toBe("pinus-sylvestris");
  });
});
