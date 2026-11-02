import { describe, it, expect } from "vitest";
import reducer, {
  setAnnotationId,
  setTaxonId,
  type WizardState,
} from "./wizardSlice";

const baseState: WizardState = {
  name: "",
  description: "",
  taxonId: null,
  annotationId: null,
};

describe("wizardSlice", () => {
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
