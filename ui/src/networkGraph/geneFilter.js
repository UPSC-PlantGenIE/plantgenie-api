import { h } from "./dom.js";
import { GENE_FILTERS } from "./logic.js";

const LABELS = {
  uncharacterized: "Show only uncharacterized genes",
  all: "Show all genes",
  annotated: "Hide genes without annotations",
};
const SHORT = {
  uncharacterized: "Uncharacterized",
  all: "All genes",
  annotated: "Annotated",
};

/** The stop (0, 1 or 2) nearest to a position along the bar (0 = left end, 1 = right end). */
export const stopAt = (pos) =>
  Math.min(
    GENE_FILTERS.length - 1,
    Math.max(0, Math.round(pos * (GENE_FILTERS.length - 1)))
  );

/**
 * Annotation filter: a rounded bar with three stops and a thumb to drag between them (like the zoom bar).
 * Left = only uncharacterized genes, middle (default) = every gene, right = hide genes without annotations.
 * Drag the thumb, click a stop, or use the arrow keys; onChange(filter) fires when the stop changes.
 */
export function createGeneFilter({ onChange }) {
  let index = GENE_FILTERS.indexOf("all");
  const label = h("div", { class: "gf-label", role: "status" });
  const thumb = h("span", { class: "gf-thumb" });
  const stops = GENE_FILTERS.map((f) =>
    h("span", { class: "gf-stop", title: LABELS[f] })
  );
  stops.forEach((s, i) => {
    s.style.left = `${(i / (GENE_FILTERS.length - 1)) * 100}%`;
  });
  const track = h(
    "div",
    {
      class: "gf-track",
      role: "slider",
      tabindex: "0",
      "aria-label": "Annotation filter",
      "aria-valuemin": "0",
      "aria-valuemax": String(GENE_FILTERS.length - 1),
    },
    ...stops,
    thumb
  );

  const place = (pos) => {
    thumb.style.left = `${pos * 100}%`;
  };
  function render() {
    const f = GENE_FILTERS[index];
    place(index / (GENE_FILTERS.length - 1));
    stops.forEach((s, i) => s.classList.toggle("on", i === index));
    label.textContent = LABELS[f];
    track.setAttribute("aria-valuenow", String(index));
    track.setAttribute("aria-valuetext", LABELS[f]);
    el.title = `${LABELS[f]}. Drag the point to change what is shown`;
  }
  function choose(next) {
    if (next === index) return;
    index = next;
    render();
    onChange(GENE_FILTERS[index]);
  }

  let dragging = false;
  const posOf = (e) => {
    const box = track.getBoundingClientRect();
    return box.width
      ? Math.min(1, Math.max(0, (e.clientX - box.left) / box.width))
      : index / (GENE_FILTERS.length - 1);
  };
  track.addEventListener("pointerdown", (e) => {
    dragging = true;
    track.setPointerCapture?.(e.pointerId);
    track.classList.add("dragging");
    place(posOf(e)); // the thumb follows the pointer...
    choose(stopAt(posOf(e))); // ...and what is shown follows the nearest stop
    e.preventDefault();
  });
  track.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    place(posOf(e));
    choose(stopAt(posOf(e)));
  });
  const release = () => {
    if (!dragging) return;
    dragging = false;
    track.classList.remove("dragging");
    render(); // ...and it settles on the stop
  };
  track.addEventListener("pointerup", release);
  track.addEventListener("pointercancel", release);
  track.addEventListener("keydown", (e) => {
    const last = GENE_FILTERS.length - 1;
    const next = {
      ArrowLeft: index - 1,
      ArrowDown: index - 1,
      ArrowRight: index + 1,
      ArrowUp: index + 1,
      Home: 0,
      End: last,
    }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    choose(Math.min(last, Math.max(0, next)));
  });

  const el = h(
    "div",
    { class: "gene-filter" },
    h(
      "div",
      { class: "gf-ends" },
      h("span", {}, SHORT.uncharacterized),
      h("span", {}, SHORT.annotated)
    ),
    track,
    label
  );
  render();

  return {
    el,
    value: () => GENE_FILTERS[index],
    set(f) {
      const i = GENE_FILTERS.indexOf(f);
      if (i >= 0) {
        index = i;
        render();
      }
    },
  };
}
