import { test, expect, beforeAll } from "vitest";
import { createGraph } from "../graph.js";

// jsdom has no canvas and no ResizeObserver; the graph only needs them to paint and to fit the frame
beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    disconnect() {}
  };
  for (const k of ["width", "height"])
    Object.defineProperty(SVGSVGElement.prototype, k, {
      configurable: true,
      get: () => ({ baseVal: { value: 800 } }),
    });
  HTMLCanvasElement.prototype.getContext = () =>
    new Proxy({}, { get: () => () => {}, set: () => true });
});

const NODES = ["a", "b", "c", "d", "e", "f"].map((id) => ({
  id,
  description: id === "f" ? "" : `gene ${id}`,
}));
// a - b - c is a chain, d - e a pair, f alone
const EDGES = [
  ["a", "b"],
  ["b", "c"],
  ["d", "e"],
].map(([source, target]) => ({ source, target, score: 0.9 }));

function setup(nodes = NODES, edges = EDGES) {
  const host = document.createElement("div");
  document.body.append(host);
  const tooltip = document.createElement("div");
  const events = { select: [], lasso: [], moved: [] };
  const graph = createGraph(host, {
    tooltip,
    onSelect: (ids) => events.select.push(ids),
    onLasso: (e) => events.lasso.push(e),
    onMoved: (e) => events.moved.push(e),
  });
  graph.setColors({ node: "#0300FC", edge: "#000000" });
  graph.setData(nodes, edges);
  graph.setThreshold(0);
  graph.setGeneFilter("all");
  return {
    host,
    graph,
    events,
    pos: (id) => {
      const [n] = graph.nodesById([id]);
      return { x: n.x, y: n.y };
    },
  };
}

const mouse = (type, x, y, extra = {}) => {
  const e = new MouseEvent(type, {
    clientX: x,
    clientY: y,
    bubbles: true,
    button: 0,
    ...extra,
  });
  Object.defineProperty(e, "view", { value: window }); // d3-drag listens for the moves on event.view
  return e;
};
/** Draw an outline around the whole canvas (every gene lies inside) or around a spot far away from them. */
function drawLasso(host, polygon) {
  const layer = host.querySelector(".lasso-layer");
  const [first, ...rest] = polygon;
  layer.dispatchEvent(mouse("pointerdown", ...first));
  for (const p of rest) layer.dispatchEvent(mouse("pointermove", ...p));
  layer.dispatchEvent(mouse("pointerup", ...polygon.at(-1)));
}
const EVERYWHERE = [
  [-9000, -9000],
  [9000, -9000],
  [9000, 9000],
  [-9000, 9000],
];
const FAR_AWAY = [
  [8000, 8000],
  [8100, 8000],
  [8100, 8100],
  [8000, 8100],
];

test("the multiple selection selects the visible genes inside the outline and reports where it ended", () => {
  const { host, graph, events } = setup();
  graph.startLasso();
  expect(host.querySelector(".lasso-layer").style.display).not.toBe("none");
  drawLasso(host, EVERYWHERE);
  expect(graph.selectedIds().sort()).toEqual(["a", "b", "c", "d", "e", "f"]);
  expect(events.lasso.at(-1).ids).toHaveLength(6);
  expect(host.querySelector(".lasso-layer").style.display).toBe("none"); // one outline per click of the button
  graph.startLasso();
  drawLasso(host, FAR_AWAY);
  expect(events.lasso.at(-1).ids).toEqual([]);
});

test("genes hidden by the annotation filter are never selected", () => {
  const { host, graph } = setup();
  graph.setGeneFilter("annotated"); // f has no description
  graph.startLasso();
  drawLasso(host, EVERYWHERE);
  expect(graph.selectedIds()).not.toContain("f");
  expect(graph.selectedIds()).toHaveLength(5);

  graph.setGeneFilter("uncharacterized"); // only f is left
  graph.startLasso();
  drawLasso(host, EVERYWHERE);
  expect(graph.selectedIds()).toEqual(["f"]);
});

test("a degenerate outline (a click) selects nothing and says it was cancelled", () => {
  const { host, graph, events } = setup();
  graph.startLasso();
  drawLasso(host, [[10, 10]]);
  expect(events.lasso.at(-1).cancelled).toBe(true);
  expect(graph.selectedIds()).toEqual([]);
});

test("dragging one of several selected genes moves them all, keeping their distances", () => {
  const { host, graph, pos } = setup();
  graph.startLasso();
  drawLasso(host, EVERYWHERE);
  const before = Object.fromEntries(
    ["a", "b", "c", "d", "e", "f"].map((id) => [id, pos(id)])
  );
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === "a"
  );
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  window.dispatchEvent(mouse("mousemove", 160, 140));
  window.dispatchEvent(mouse("mouseup", 160, 140));
  for (const id of Object.keys(before)) {
    const now = pos(id);
    expect(now.x - before[id].x).toBeCloseTo(60, 5);
    expect(now.y - before[id].y).toBeCloseTo(40, 5);
  }
});

test("dropping several dragged genes reports them and where the pointer ended; a press without moving reports nothing", () => {
  const { host, graph, events } = setup();
  graph.startLasso();
  drawLasso(host, EVERYWHERE);
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === "a"
  );
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  window.dispatchEvent(mouse("mouseup", 100, 100));
  expect(events.moved).toEqual([]);
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  window.dispatchEvent(mouse("mousemove", 160, 140));
  window.dispatchEvent(mouse("mouseup", 160, 140));
  expect(events.moved).toHaveLength(1);
  expect(events.moved[0].ids.sort()).toEqual(["a", "b", "c", "d", "e", "f"]);
  expect(events.moved[0].at).toEqual([160, 140]);
});

test("dragging a single gene pulls its connected genes along, stickily (they trail behind and settle)", async () => {
  const { host, graph, pos } = setup();
  const a0 = pos("a"),
    b0 = pos("b"),
    c0 = pos("c"),
    d0 = pos("d");
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === "a"
  );
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  window.dispatchEvent(mouse("mousemove", 400, 100)); // 300px to the right
  await new Promise((r) => setTimeout(r, 400));
  const a1 = pos("a"),
    b1 = pos("b"),
    c1 = pos("c");
  expect(a1.x - a0.x).toBeCloseTo(300, 5); // the dragged gene follows the pointer exactly
  expect(b1.x - b0.x).toBeGreaterThan(40); // its neighbour is pulled along...
  expect(b1.x - b0.x).toBeLessThan(a1.x - a0.x); // ...but not rigidly
  expect(Math.abs(c1.x - c0.x)).toBeGreaterThan(5); // two steps out still feel it
  expect(pos("d")).toEqual(d0); // genes that are not connected stay put
  window.dispatchEvent(mouse("mouseup", 400, 100));
  await new Promise((r) => setTimeout(r, 1500)); // after the drop everything settles by itself
  const settled = pos("b");
  await new Promise((r) => setTimeout(r, 300));
  expect(pos("b").x).toBeCloseTo(settled.x, 0);
  expect(graph.selectedIds()).toEqual([]);
}, 10000);

const geneNodes = (ids) => ids.map((id) => ({ id, description: id }));
const geneEdges = (pairs) =>
  pairs.map(([source, target, score]) => ({ source, target, score }));

async function dragAndMeasure(nodes, edges, draggedId, placements = {}) {
  const { host, graph, pos } = setup(nodes, edges);
  for (const [id, [x, y]] of Object.entries(placements)) {
    const [node] = graph.nodesById([id]);
    node.x = x;
    node.y = y;
  }
  const before = Object.fromEntries(nodes.map((n) => [n.id, pos(n.id)]));
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === draggedId
  );
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  for (let step = 1; step <= 30; step++) {
    window.dispatchEvent(mouse("mousemove", 100 + step * 10, 100));
    await new Promise((r) => setTimeout(r, 16));
  }
  const followed = (id) => pos(id).x - before[id].x;
  const result = Object.fromEntries(nodes.map((n) => [n.id, followed(n.id)]));
  window.dispatchEvent(mouse("mouseup", 400, 100));
  await new Promise((r) => setTimeout(r, 50));
  return result;
}

test("relatives follow a dragged gene less the further away they are, down to the third generation", async () => {
  const followed = await dragAndMeasure(
    geneNodes(["p", "q", "r", "s"]),
    geneEdges([
      ["p", "q", 0.9],
      ["q", "r", 0.9],
      ["r", "s", 0.9],
    ]),
    "p"
  );
  expect(followed.q).toBeGreaterThan(followed.r);
  expect(followed.r).toBeGreaterThan(followed.s);
  expect(followed.s).toBeGreaterThan(2);
});

const FIRST_RELATIVES = [0, 1, 2, 3, 4, 5].map((i) => `q${i}`);
const DENSE_NODES = geneNodes([
  "p",
  ...FIRST_RELATIVES,
  ...Array.from({ length: 18 }, (_, i) => `r${i}`),
]);
const DENSE_EDGES = geneEdges([
  ...FIRST_RELATIVES.map((id) => ["p", id, 0.9]),
  ...Array.from({ length: 18 }, (_, i) => [
    `q${Math.floor(i / 3)}`,
    `r${i}`,
    0.9,
  ]),
  ...Array.from({ length: 18 }, (_, i) => [
    `q${(Math.floor(i / 3) + 1) % 6}`,
    `r${i}`,
    0.9,
  ]),
]);
const meanOf = (values) =>
  values.reduce((sum, value) => sum + value, 0) / values.length;

test("in a dense cluster the first relatives still follow at least 40% of the drag while the gene is dragged", async () => {
  const followed = await dragAndMeasure(DENSE_NODES, DENSE_EDGES, "p");
  expect(meanOf(FIRST_RELATIVES.map((id) => followed[id]))).toBeGreaterThan(
    0.4 * 300
  );
});

test("first relatives do not creep back towards their old place after the gene is dropped", async () => {
  const { host, pos } = setup(DENSE_NODES, DENSE_EDGES);
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === "p"
  );
  const meanX = () => meanOf(FIRST_RELATIVES.map((id) => pos(id).x));
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  for (let step = 1; step <= 30; step++) {
    window.dispatchEvent(mouse("mousemove", 100 + step * 10, 100));
    await new Promise((r) => setTimeout(r, 16));
  }
  window.dispatchEvent(mouse("mouseup", 400, 100));
  const atDrop = meanX();
  await new Promise((r) => setTimeout(r, 1500));
  expect(meanX()).toBeGreaterThan(atDrop - 1);
}, 10000);

test("a relative joined by a stronger edge is held harder than one joined by a weaker edge", async () => {
  const followed = await dragAndMeasure(
    geneNodes(["x", "y", "z"]),
    geneEdges([
      ["x", "y", 0.95],
      ["x", "z", 0.65],
    ]),
    "x",
    { x: [400, 300], y: [460, 260], z: [460, 340] }
  ); // y and z lie symmetrically around x: only the edge score differs
  expect(followed.y - followed.z).toBeGreaterThan(4);
});

test("the genes gathered around a clicked gene stay there until it is unselected", async () => {
  const { host, graph, pos } = setup();
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === "b"
  );
  const distanceToB = (id) =>
    Math.hypot(pos(id).x - pos("b").x, pos(id).y - pos("b").y);
  circle.dispatchEvent(mouse("mousedown", 0, 0));
  window.dispatchEvent(mouse("mouseup", 0, 0));
  circle.dispatchEvent(mouse("click", 0, 0));
  await new Promise((r) => setTimeout(r, 1500));
  const gathered = distanceToB("a");
  expect(gathered).toBeCloseTo(35, 0);
  await new Promise((r) => setTimeout(r, 1500));
  expect(distanceToB("a")).toBeCloseTo(gathered, 5);
  expect(distanceToB("c")).toBeCloseTo(gathered, 0);
  graph.clearSelection();
  await new Promise((r) => setTimeout(r, 700));
  expect(distanceToB("a")).toBeGreaterThan(gathered + 3);
}, 15000);

test("resetting the positions glides every gene back to where the layout put it and clears the selection", async () => {
  const { host, graph, pos } = setup();
  const ids = ["a", "b", "c", "d", "e", "f"];
  const initial = Object.fromEntries(ids.map((id) => [id, pos(id)]));
  const circleOf = (id) =>
    [...host.querySelectorAll("circle")].find((c) => c.__data__.id === id);
  circleOf("a").dispatchEvent(mouse("mousedown", 100, 100));
  window.dispatchEvent(mouse("mousemove", 400, 300));
  window.dispatchEvent(mouse("mouseup", 400, 300));
  await new Promise((r) => setTimeout(r, 50));
  circleOf("e").dispatchEvent(mouse("mousedown", 0, 0));
  window.dispatchEvent(mouse("mouseup", 0, 0));
  circleOf("e").dispatchEvent(mouse("click", 0, 0));
  expect(Math.abs(pos("a").x - initial.a.x)).toBeGreaterThan(50);
  expect(graph.selectedIds()).toEqual(["e"]);
  graph.resetPositions();
  await new Promise((r) => setTimeout(r, 1000));
  for (const id of ids) {
    expect(pos(id).x).toBeCloseTo(initial[id].x, 3);
    expect(pos(id).y).toBeCloseTo(initial[id].y, 3);
  }
  expect(graph.selectedIds()).toEqual([]);
}, 15000);

test("the genes gathered around a selected gene stay put when the multiple selection takes over", () => {
  const { host, graph, pos } = setup();
  const circle = [...host.querySelectorAll("circle")].find(
    (c) => c.__data__.id === "b"
  );
  circle.dispatchEvent(mouse("click", 0, 0)); // selects b: its neighbours gather around it (animated)
  expect(graph.selectedIds()).toEqual(["b"]);
  graph.startLasso();
  const before = pos("a");
  drawLasso(host, EVERYWHERE);
  expect(pos("a")).toEqual(before); // selecting many does not send anything back to its old place
  expect(graph.selectedIds().sort()).toEqual(["a", "b", "c", "d", "e", "f"]);
});
