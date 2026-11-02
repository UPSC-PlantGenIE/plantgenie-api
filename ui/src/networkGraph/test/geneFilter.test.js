// @vitest-environment jsdom
import { test } from "vitest";
import assert from "node:assert/strict";
import { createGeneFilter, stopAt } from "../geneFilter.js";

test("the stops sit at the two ends and the middle", () => {
  assert.deepEqual(
    [0, 0.24, 0.26, 0.5, 0.74, 0.76, 1].map(stopAt),
    [0, 0, 1, 1, 1, 2, 2]
  );
  assert.equal(stopAt(-3), 0);
  assert.equal(stopAt(9), 2);
});

test("it starts in the middle: show all genes", () => {
  const f = createGeneFilter({ onChange() {} });
  assert.equal(f.value(), "all");
  assert.match(f.el.textContent, /Show all genes/);
});

test("arrow keys move it left (uncharacterized only) and right (hide genes without annotations)", () => {
  const seen = [];
  const f = createGeneFilter({ onChange: (v) => seen.push(v) });
  const track = f.el.querySelector(".gf-track");
  const press = (key) =>
    track.dispatchEvent(
      new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true })
    );
  press("ArrowLeft");
  assert.equal(f.value(), "uncharacterized");
  assert.match(f.el.textContent, /Show only uncharacterized genes/);
  press("ArrowLeft"); // already at the end: nothing changes
  press("ArrowRight");
  press("ArrowRight");
  assert.equal(f.value(), "annotated");
  assert.match(f.el.textContent, /Hide genes without annotations/);
  assert.deepEqual(seen, ["uncharacterized", "all", "annotated"]);
  assert.equal(
    track.getAttribute("aria-valuetext"),
    "Hide genes without annotations"
  );
});

test("dragging the thumb picks the nearest stop", () => {
  const seen = [];
  const f = createGeneFilter({ onChange: (v) => seen.push(v) });
  const track = f.el.querySelector(".gf-track");
  track.getBoundingClientRect = () => ({
    left: 100,
    width: 100,
    top: 0,
    height: 14,
    right: 200,
    bottom: 14,
  });
  const fire = (type, clientX) =>
    track.dispatchEvent(
      Object.assign(new Event(type, { bubbles: true, cancelable: true }), {
        clientX,
        pointerId: 1,
      })
    );
  fire("pointerdown", 150);
  fire("pointermove", 195);
  fire("pointermove", 102);
  fire("pointerup", 102);
  assert.deepEqual(seen, ["annotated", "uncharacterized"]);
  assert.equal(f.value(), "uncharacterized");
});
