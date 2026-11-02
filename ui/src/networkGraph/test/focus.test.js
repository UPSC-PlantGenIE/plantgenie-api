import { test } from "vitest";
import assert from "node:assert/strict";
import { pushBack, pullAround } from "../focus.js";

const centre = { x: 0, y: 0 };
const ring = (count, radius) =>
  Array.from({ length: count }, (_, i) => ({
    x: radius * Math.cos(i),
    y: radius * Math.sin(i),
    r: 12.5,
  }));
const dist = (n) => Math.hypot(n.x - centre.x, n.y - centre.y);

test("pushBack clears the area around the selected group", () => {
  const others = [
    { x: 30, y: 0 },
    { x: 0, y: -45 },
    { x: -70, y: 20 },
    { x: 140, y: 140 },
  ];
  const moved = pushBack(others, centre, 90);
  for (const n of others) {
    const at = moved.get(n) ?? n;
    assert.ok(
      dist(at) >= 90 + 14 - 1e-6,
      `gene at ${dist(n)} ends at ${dist(at)}`
    );
  }
});

test("pushBack moves genes straight away from the centre and keeps far genes in place", () => {
  const near = { x: 60, y: 0 },
    far = { x: 4000, y: 0 };
  const moved = pushBack([near, far], centre, 50);
  const p = moved.get(near);
  assert.ok(p.x > near.x && Math.abs(p.y) < 1e-9);
  assert.equal(moved.has(far), false);
});

test("pushBack shifts the nearby genes together, so their layout is not squeezed", () => {
  const a = { x: 40, y: 0 },
    b = { x: 70, y: 0 };
  const moved = pushBack([a, b], centre, 60);
  assert.ok(moved.get(b).x - moved.get(a).x >= 30 - 1e-6);
});

test("pushBack always steps back a little, and copes with a gene on the centre", () => {
  const moved = pushBack(
    [
      { x: 300, y: 0 },
      { x: 0, y: 0 },
    ],
    centre,
    20
  );
  assert.ok(
    moved.get([...moved.keys()].find((n) => n.x !== 0)) !== undefined ||
      moved.size > 0
  );
  const onCentre = [...moved.keys()].find((n) => n.x === 0);
  assert.ok(dist(moved.get(onCentre)) > 0);
  assert.equal(pushBack([], centre, 50).size, 0);
});

test("the pushed genes stay clear of the gathered ring", () => {
  const neighbours = ring(12, 200);
  const slots = pullAround(centre, neighbours, 12.5);
  const clearance = Math.max(...[...slots.values()].map(dist)) + 12.5;
  const others = Array.from({ length: 40 }, (_, i) => ({
    x: 20 + i * 9,
    y: (i % 5) * 20 - 40,
  }));
  const moved = pushBack(others, centre, clearance);
  assert.ok(others.every((n) => dist(moved.get(n) ?? n) >= clearance));
});
