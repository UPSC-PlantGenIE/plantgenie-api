import { test } from "vitest";
import assert from "node:assert/strict";
import {
  binOf,
  edgeWidth,
  visibleEdges,
  geneStats,
  rank,
  matrixTsv,
  BINS,
} from "../logic.js";
import { buildColorModes } from "../colorModes.js";
import * as G from "../groups.js";
import { louvain, groupUnlinked } from "../cluster.js";
import {
  hsvToRgb,
  rgbToHsv,
  rgbToHsl,
  hslToRgb,
  toHex,
  parseHex,
} from "../colorPicker.js";
import { randomNodeColor, PALETTES } from "../palettes.js";

const nodes = [{ id: "a" }, { id: "b" }, { id: "c" }, { id: "d" }];
const edges = [
  { source: "a", target: "b", score: 0.9 },
  { source: "a", target: "c", score: 0.5 },
  { source: "b", target: "d", score: 0.7 },
];

test("bins are monotonic and cover 0..1", () => {
  assert.equal(binOf(0.01), 0);
  assert.equal(binOf(0.25), 1);
  assert.equal(binOf(0.74), 2);
  assert.equal(binOf(1), 3);
  assert.ok(edgeWidth(0.9) > edgeWidth(0.1));
});

test("threshold is strictly greater-than", () => {
  assert.equal(visibleEdges(nodes, edges, 0.7).length, 1);
  assert.equal(visibleEdges(nodes, edges, 0.5).length, 2);
  assert.equal(visibleEdges(nodes, edges, 0).length, 3);
});

test("stats: degree and score sum, no zeros", () => {
  const s = Object.fromEntries(geneStats(edges).map((x) => [x.id, x]));
  assert.equal(s.a.degree, 2);
  assert.equal(s.a.sum, 1.4);
  assert.equal(s.b.sum, 1.6);
  assert.ok(!("z" in s));
});

test("rank: collapsed uses fit, expanded keeps ties with the 10th", () => {
  const stats = Array.from({ length: 14 }, (_, i) => ({
    id: "g" + String(i).padStart(2, "0"),
    degree: i < 9 ? 20 - i : i < 12 ? 5 : 3,
    sum: 0,
  }));
  // values: 20..12 (9 genes), then 3 genes with 5, then 2 with 3
  assert.equal(rank(stats, "degree", { expanded: false, fit: 4 }).length, 4);
  const exp = rank(stats, "degree", { expanded: true, fit: 4 });
  assert.equal(exp.length, 12); // 10th value is 5 -> all three 5s included, the 3s excluded
  assert.equal(rank(stats, "sum", { expanded: true, fit: 4 }).length, 0); // zero scores never shown
});

test("rank: fewer than 10 non-zero genes", () => {
  const stats = [
    { id: "x", degree: 2, sum: 1 },
    { id: "y", degree: 0, sum: 0 },
  ];
  assert.deepEqual(
    rank(stats, "degree", { expanded: true, fit: 3 }).map((s) => s.id),
    ["x"]
  );
});

test("matrix tsv is symmetric", () => {
  const t = matrixTsv(nodes, edges)
    .trim()
    .split("\n")
    .map((l) => l.split("\t"));
  assert.equal(t[0].join(), "gene,a,b,c,d");
  assert.equal(t[1][2], "0.9");
  assert.equal(t[2][1], "0.9");
});

test("the gene colour comes from the default palette", () => {
  assert.ok(PALETTES[0].colors.includes(randomNodeColor()));
  assert.equal(
    randomNodeColor(() => 0),
    PALETTES[0].colors[0]
  );
  assert.equal(
    randomNodeColor(() => 0.999),
    PALETTES[0].colors.at(-1)
  );
});

test("edges get thicker and darker with the score: pitch black and 2px at score 1, a faint hairline at the bottom", () => {
  assert.deepEqual(
    BINS.map((b) => b.width),
    [0.25, 0.6, 1.2, 2]
  );
  assert.deepEqual(
    BINS.map((b) => b.opacity),
    [0.12, 0.3, 0.6, 1]
  );
  assert.equal(edgeWidth(1), 2);
  assert.equal(edgeWidth(0.1), 0.25);
});

test("customize colours the genes of the list and the edges", () => {
  const colors = { node: "#111111", edge: "#000000" };
  const modes = buildColorModes(colors, "My list");
  assert.deepEqual(
    modes.getModes().map((m) => m.id),
    ["nodes", "edges"]
  );
  const [genes] = modes.getItems("nodes");
  assert.equal(genes.label, "My list");
  genes.set("#123456");
  assert.equal(colors.node, "#123456");
  const [lines] = modes.getItems("edges");
  assert.equal(lines.get(), "#000000");
  lines.set("#abcdef");
  assert.equal(colors.edge, "#abcdef");
});

// ---- palette view model ----
const SW = ["#6DFD9D", "#6DE7FD", "#FDF16D"];
const itm = (key, color) => ({ key, get: () => color });

test("groups: items already on a swatch share its box, others start in the tray", () => {
  const g = G.initGroups(
    [itm("a", "#6dfd9d"), itm("b", "#6DFD9D"), itm("c", "#123456")],
    SW
  );
  assert.equal(g.length, 2);
  assert.deepEqual(g[0].keys, ["a", "b"]);
  assert.equal(g[0].color, "#6dfd9d");
  assert.deepEqual(g[1].keys, ["c"]);
  assert.equal(g[1].color, null);
});

test("groups: dropping boxes on the same colour merges them (same colour for all)", () => {
  let gs = G.initGroups([itm("a", "x"), itm("b", "x"), itm("c", "x")], SW);
  const [A, B, C] = gs.map((g) => g.id);
  let r = G.placeOnColor(gs, A, "#6DE7FD");
  gs = r.groups;
  assert.deepEqual(r.keys, ["a"]);
  r = G.placeOnColor(gs, B, "#6DE7FD");
  gs = r.groups;
  assert.equal(gs.length, 2);
  assert.deepEqual(gs.find((g) => g.color).keys, ["a", "b"]);
  r = G.mergeGroups(gs, C, gs.find((g) => g.color).id); // box on box
  assert.equal(r.color, "#6de7fd");
  assert.deepEqual(r.keys, ["c"]);
  assert.deepEqual(r.groups[0].keys, ["a", "b", "c"]);
});

test("groups: dragging a name out of a merged box gives it its own box in the tray", () => {
  const gs = G.initGroups([itm("a", "#6DFD9D"), itm("b", "#6DFD9D")], SW);
  const out = G.detachKey(gs, "b");
  assert.deepEqual(out.find((g) => g.color).keys, ["a"]);
  assert.deepEqual(out.find((g) => !g.color).keys, ["b"]);
  const sole = G.detachKey(G.initGroups([itm("a", "#6DFD9D")], SW), "a"); // a lone box is simply unplaced
  assert.equal(sole.length, 1);
  assert.equal(sole[0].color, null);
  const r = G.placeKeyOnColor(gs, "b", "#FDF16D");
  assert.deepEqual(r.keys, ["b"]);
  assert.equal(r.groups.length, 2);
  const m = G.moveKeyToGroup(gs, "b", gs[0].id);
  assert.deepEqual(m.groups[0].keys, ["a", "b"]);
});

// ---- picker maths ----
test("colour conversions round-trip", () => {
  assert.deepEqual(hsvToRgb({ h: 0, s: 1, v: 1 }), [255, 0, 0]);
  assert.deepEqual(
    hsvToRgb({ h: 200, s: 0.5, v: 0.5 }),
    hsvToRgb(rgbToHsv(hsvToRgb({ h: 200, s: 0.5, v: 0.5 })))
  );
  for (const rgb of [
    [109, 231, 253],
    [0, 0, 0],
    [255, 255, 255],
    [18, 52, 86],
  ]) {
    hslToRgb(rgbToHsl(rgb)).forEach((v, k) =>
      assert.ok(Math.abs(v - rgb[k]) <= 2)
    ); // HSL is shown in whole numbers
    assert.deepEqual(hsvToRgb(rgbToHsv(rgb)), rgb);
  }
  assert.equal(toHex([109, 231, 253]), "#6de7fd");
  assert.equal(toHex([109, 231, 253], 0.5), "#6de7fd80");
});

test("hex parsing accepts 3/6/8 digits and rejects junk", () => {
  assert.deepEqual(parseHex("#6DE7FD"), { rgb: [109, 231, 253], a: 1 });
  assert.deepEqual(parseHex("fff").rgb, [255, 255, 255]);
  assert.ok(Math.abs(parseHex("#00000080").a - 0.5) < 0.01);
  assert.equal(parseHex("#12"), null);
  assert.equal(parseHex("zzzzzz"), null);
});

// ---- grouping ----
const clique = (ids, w = 0.9) =>
  ids.flatMap((a, i) =>
    ids.slice(i + 1).map((b) => ({ source: a, target: b, weight: w }))
  );

test("louvain: separates groups of strongly connected genes joined by weak links", () => {
  const links = [
    ...clique([0, 1, 2, 3, 4]),
    ...clique([5, 6, 7, 8, 9]),
    { source: 4, target: 5, weight: 0.1 },
  ];
  const c = louvain(10, links);
  assert.equal(new Set(c).size, 2);
  assert.ok(
    [0, 1, 2, 3, 4].every((i) => c[i] === c[0]) &&
      [5, 6, 7, 8, 9].every((i) => c[i] === c[5]) &&
      c[0] !== c[5]
  );
});

test("louvain: isolated genes stay on their own, result is deterministic and ids are 0..k-1", () => {
  const links = clique([0, 1, 2]);
  const c = louvain(5, links);
  assert.equal(c[3] !== c[4] && c[3] !== c[0], true);
  assert.deepEqual([...louvain(5, links)], [...c]);
  assert.deepEqual([...new Set(c)].sort(), [0, 1, 2]);
  assert.equal(louvain(3, []).length, 3);
});

test("groupUnlinked: genes without links share one group, ids stay 0..k-1 without gaps", () => {
  // 6 genes; 0-1 and 2-3 linked (louvain gave them 0 and 1), 4 and 5 were singletons (ids 2 and 3)
  const comm = Int32Array.from([0, 0, 1, 1, 2, 3]);
  const out = groupUnlinked(comm, [
    { source: 0, target: 1 },
    { source: 2, target: 3 },
  ]);
  assert.deepEqual([...out], [0, 0, 1, 1, 2, 2]);
  assert.deepEqual(
    [...groupUnlinked(Int32Array.from([0, 1, 2]), [])],
    [0, 0, 0]
  );
  const gap = groupUnlinked(Int32Array.from([0, 2, 2, 5]), [
    { source: 1, target: 2 },
  ]);
  assert.deepEqual([...gap], [0, 1, 1, 0]); // 0 and 3 are unlinked -> one group; no id is skipped
});

// ---------- annotation filter ----------
test("uncharacterized = no description; the filter keeps one side or everything", async () => {
  const { isUncharacterized, nodeVisible, GENE_FILTERS } =
    await import("../logic.js");
  const plain = { id: "p", description: "kinase" };
  const blank = { id: "b", description: "" };
  const spaces = { id: "s", description: "   " };
  const missing = { id: "m" };
  assert.deepEqual(GENE_FILTERS, ["uncharacterized", "all", "annotated"]);
  assert.deepEqual([plain, blank, spaces, missing].map(isUncharacterized), [
    false,
    true,
    true,
    true,
  ]);
  const shown = (f) =>
    [plain, blank, spaces, missing]
      .filter((n) => nodeVisible(n, f))
      .map((n) => n.id);
  assert.deepEqual(shown("all"), ["p", "b", "s", "m"]);
  assert.deepEqual(shown("uncharacterized"), ["b", "s", "m"]);
  assert.deepEqual(shown("annotated"), ["p"]);
});

test("the filter removes edges of the genes it hides", () => {
  const ns = [
    { id: "a", description: "x" },
    { id: "b", description: "y" },
    { id: "c", description: "" },
  ];
  const es = [
    { source: "a", target: "b", score: 0.9 },
    { source: "a", target: "c", score: 0.9 },
  ];
  assert.equal(visibleEdges(ns, es, 0, "all").length, 2);
  assert.deepEqual(
    visibleEdges(ns, es, 0, "annotated").map((e) => e.target),
    ["b"]
  );
  assert.equal(visibleEdges(ns, es, 0, "uncharacterized").length, 0);
});

test("the graph opens with only the edges above 0.6", async () => {
  const { DEFAULT_THRESHOLD } = await import("../view.js");
  assert.equal(DEFAULT_THRESHOLD, 0.6);
  const ns = [{ id: "a" }, { id: "b" }, { id: "c" }];
  const es = [
    { source: "a", target: "b", score: 0.9 },
    { source: "a", target: "c", score: 0.3 },
  ];
  assert.deepEqual(
    visibleEdges(ns, es, DEFAULT_THRESHOLD).map((e) => e.target),
    ["b"]
  );
});

test("statistics count every edge the same way", () => {
  const es = [
    { source: "a", target: "b", score: 1 },
    { source: "a", target: "c", score: 0.5 },
  ];
  const s = Object.fromEntries(geneStats(es).map((x) => [x.id, x]));
  assert.equal(s.a.degree, 2);
  assert.equal(s.a.sum, 1.5);
  assert.equal(s.b.sum, 1);
});

// ---------- palettes, outlines, edge colours ----------
test("the palettes are the design ones: Viz Gold first (the default), the rest in order", async () => {
  const { PALETTES, DEFAULT_EDGE_COLOR } = await import("../palettes.js");
  assert.deepEqual(
    PALETTES.map((p) => p.name),
    [
      "Viz Gold",
      "Vivid light",
      "Faded light",
      "Solid",
      "Paired",
      "Dark",
      "Neon",
    ]
  );
  assert.deepEqual(
    PALETTES.map((p) => p.colors.length),
    [7, 8, 12, 9, 12, 7, 7]
  );
  for (const p of PALETTES) {
    assert.ok(
      p.colors.every((c) => /^#[0-9A-F]{6}$/.test(c)),
      p.name
    );
    assert.equal(
      new Set(p.colors).size,
      p.colors.length,
      `${p.name} repeats a colour`
    );
  }
  assert.deepEqual(PALETTES[0].colors.slice(0, 3), [
    "#0300FC",
    "#9E00D7",
    "#CE34B6",
  ]); // blue, purple, magenta
  // the edge colour is not one of the default palette's colours, so an edge never looks tied to the genes
  assert.equal(DEFAULT_EDGE_COLOR, "#000000");
  assert.ok(!PALETTES[0].colors.includes(DEFAULT_EDGE_COLOR));
});

test("a node outline is its own colour, a little darker", async () => {
  const { darken, hexToRgb } = await import("../logic.js");
  for (const c of ["#FFFF29", "#0300FC", "#324476", "#FFFFFF"]) {
    const [a, b] = [hexToRgb(c), hexToRgb(darken(c))];
    assert.ok(
      a.every((v, i) => b[i] <= v),
      c
    ); // never lighter
    assert.ok(b.some((v, i) => v < a[i]) || c === "#000000", c); // and visibly darker, light colours and dark ones alike
  }
  assert.equal(darken("#FFFFFF"), "#c7c7c7");
  assert.equal(darken("not a colour"), "not a colour");
});
