import { test, expect, beforeAll, afterEach, vi } from "vitest";
import { createGraphView } from "../view.js";

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
afterEach(() => {
  document.body.replaceChildren();
});

const NODES = ["a", "b", "c", "d"].map((id) => ({
  id,
  description: `gene ${id}`,
}));
const EDGES = [
  { source: "a", target: "b", score: 0.9 },
  { source: "c", target: "d", score: 0.9 },
];

const mouse = (type, x, y) => {
  const event = new MouseEvent(type, {
    clientX: x,
    clientY: y,
    bubbles: true,
    button: 0,
  });
  Object.defineProperty(event, "view", { value: window });
  return event;
};
const press = (root, label) =>
  [...root.querySelectorAll("button")]
    .find((button) => button.textContent === label)
    .click();

function openView(api) {
  const view = createGraphView({
    api,
    listId: "L1",
    listName: "List 1",
    annotationId: "sp-v1",
    taxonName: "Species",
    colors: { node: "#0300FC", edge: "#000000" },
    onBack() {},
  });
  document.body.append(view.el);
  return view;
}

const fakeApi = (overrides = {}) => ({
  experiments: async () => [],
  graph: async () => ({ nodes: NODES, edges: EDGES }),
  exportList: async () => {},
  ...overrides,
});

test("asks for the experiments of the list's annotation and the graph of the list", async () => {
  const experiments = vi.fn(async () => []);
  const graph = vi.fn(async () => ({ nodes: NODES, edges: EDGES }));
  const view = openView(fakeApi({ experiments, graph }));

  await vi.waitFor(() =>
    expect(view.el.querySelectorAll("circle")).toHaveLength(4)
  );
  expect(experiments).toHaveBeenCalledWith("sp-v1");
  expect(graph).toHaveBeenCalledWith({
    listId: "L1",
    geneIds: null,
    experimentIds: [],
  });
});

async function openWithEverythingSelected(api = fakeApi()) {
  const view = openView(api);
  await vi.waitFor(() =>
    expect(view.el.querySelectorAll("circle")).toHaveLength(4)
  );
  view.el.querySelector(".lasso-btn").click();
  const layer = view.el.querySelector(".lasso-layer");
  layer.dispatchEvent(mouse("pointerdown", -9000, -9000));
  for (const [x, y] of [
    [9000, -9000],
    [9000, 9000],
    [-9000, 9000],
  ])
    layer.dispatchEvent(mouse("pointermove", x, y));
  layer.dispatchEvent(mouse("pointerup", -9000, 9000));
  const menu = view.el.querySelector(".lasso-menu");
  expect(menu.hidden).toBe(false);
  return { view, menu };
}

test("the options box stays while panning the graph", async () => {
  const { view, menu } = await openWithEverythingSelected();
  const svg = view.el.querySelector(".graph-svg");
  svg.dispatchEvent(mouse("pointerdown", 300, 300));
  svg.dispatchEvent(mouse("mousedown", 300, 300));
  window.dispatchEvent(mouse("mousemove", 360, 340));
  window.dispatchEvent(mouse("mouseup", 360, 340));
  expect(menu.hidden).toBe(false);
});

test("Position reset sits under Multiple selection and clears the selection with its options box", async () => {
  const { view, menu } = await openWithEverythingSelected();
  const tools = [...view.el.querySelector(".graph-tools-top").children].map(
    (child) => child.textContent.trim()
  );
  expect(tools.slice(-2)).toEqual(["Multiple selection", "Position reset"]);
  press(view.el, "Position reset");
  expect(menu.hidden).toBe(true);
  expect([...view.el.querySelectorAll("circle.selected")]).toEqual([]);
});

test("the options box comes back after inspecting, after exporting, and after moving the genes", async () => {
  const { view, menu } = await openWithEverythingSelected();

  press(menu, "Inspect");
  expect(menu.hidden).toBe(true);
  press(view.el.querySelector(".overlay"), "Close");
  expect(menu.hidden).toBe(false);

  press(menu, "Export to a new list");
  expect(menu.hidden).toBe(true);
  press(view.el.querySelector(".overlay"), "Cancel");
  expect(menu.hidden).toBe(false);

  press(menu, "Export to a new list");
  press(view.el.querySelector(".overlay"), "Create list");
  await vi.waitFor(() => expect(menu.hidden).toBe(false));

  document.dispatchEvent(
    new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
  );
  expect(menu.hidden).toBe(true);
  const circle = [...view.el.querySelectorAll("circle")].find(
    (node) => node.__data__.id === "a"
  );
  circle.dispatchEvent(mouse("mousedown", 100, 100));
  window.dispatchEvent(mouse("mousemove", 160, 140));
  window.dispatchEvent(mouse("mouseup", 160, 140));
  expect(menu.hidden).toBe(false);
});
