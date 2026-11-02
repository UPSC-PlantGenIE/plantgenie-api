// Pure graph logic (no DOM) – unit tested in test/logic.test.js.

// Four classes shown in the legend; width in px, opacity 0-1. The stronger the score, the thicker and the darker the line:
// pitch black and 2px at the top, a faint hairline at the bottom, so the classes can be told apart by eye.
export const BINS = [
  { min: 0, max: 0.25, width: 0.25, opacity: 0.12 },
  { min: 0.25, max: 0.5, width: 0.6, opacity: 0.3 },
  { min: 0.5, max: 0.75, width: 1.2, opacity: 0.6 },
  { min: 0.75, max: 1, width: 2, opacity: 1 },
];

export function binOf(score) {
  const i = BINS.findIndex((b) => score < b.max);
  return i === -1 ? BINS.length - 1 : i;
}
export const edgeWidth = (score) => BINS[binOf(score)].width;

/** The annotation filter: only the uncharacterized genes, every gene, or only the genes that have an annotation. */
export const GENE_FILTERS = ["uncharacterized", "all", "annotated"];

/** A gene without an annotation (no description) is "uncharacterized". */
export const isUncharacterized = (node) =>
  !node.description || !node.description.trim();

/** A gene is hidden when the annotation filter excludes it. */
export const nodeVisible = (node, geneFilter = "all") =>
  geneFilter === "all" ||
  (geneFilter === "uncharacterized") === isUncharacterized(node);

/** Edges whose score is greater than `threshold` and whose two genes are visible. */
export function visibleEdges(nodes, edges, threshold, geneFilter = "all") {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  return edges.filter((e) => {
    const s = byId.get(idOf(e.source)),
      t = byId.get(idOf(e.target));
    return (
      e.score > threshold &&
      s &&
      t &&
      nodeVisible(s, geneFilter) &&
      nodeVisible(t, geneFilter)
    );
  });
}
// d3.forceLink replaces ids by node objects
export const idOf = (x) => (typeof x === "object" ? x.id : x);

const round4 = (x) => Math.round(x * 1e4) / 1e4;

/** Per gene: number of connected edges and the sum of their scores. */
export function geneStats(edges) {
  const m = new Map();
  const bump = (id, score) => {
    const s = m.get(id) || { id, degree: 0, sum: 0 };
    s.degree += 1;
    s.sum += score;
    m.set(id, s);
  };
  for (const e of edges) {
    bump(idOf(e.source), e.score);
    bump(idOf(e.target), e.score);
  }
  for (const s of m.values()) s.sum = round4(s.sum);
  return [...m.values()];
}

/**
 * Rank genes by `key`, dropping zero scores.
 * collapsed: the first `fit` genes. expanded: the top 10 plus every gene tied with the 10th.
 */
export function rank(stats, key, { expanded, fit }) {
  const sorted = stats
    .filter((s) => s[key] > 0)
    .sort((a, b) => b[key] - a[key] || a.id.localeCompare(b.id));
  if (!expanded) return sorted.slice(0, Math.max(1, fit));
  if (sorted.length <= 10) return sorted;
  const cut = sorted[9][key];
  return sorted.filter((s, i) => i < 10 || s[key] === cut);
}

/** Adjacency matrix (TSV text) of the given nodes/edges; cell = edge score or 0. */
export function matrixTsv(nodes, edges) {
  const idx = new Map(nodes.map((n, i) => [n.id, i]));
  const m = nodes.map(() => new Array(nodes.length).fill(0));
  for (const e of edges) {
    const a = idx.get(idOf(e.source)),
      b = idx.get(idOf(e.target));
    if (a !== undefined && b !== undefined) m[a][b] = m[b][a] = e.score;
  }
  return (
    [
      ["gene", ...nodes.map((n) => n.id)].join("\t"),
      ...nodes.map((n, i) => [n.id, ...m[i]].join("\t")),
    ].join("\n") + "\n"
  );
}

// ---------- colours ----------
export const hexToRgb = (c) =>
  [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
export const rgbToHex = (rgb) =>
  "#" + rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");

/** The same colour, a little darker (each channel scaled down): the outline of a node. */
export const darken = (hex, factor = 0.78) =>
  /^#[0-9a-f]{6}/i.test(hex)
    ? rgbToHex(hexToRgb(hex).map((v) => v * factor))
    : hex;
