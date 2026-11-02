import {
  h,
  append,
  clear,
  onOutsideClick,
  lineSample,
  makeDraggable,
} from "./dom.js";
import { confirmDeleteGenes, deleteConfirmSkipped } from "./confirm.js";
import { createGraph, ZOOM_RANGE } from "./graph.js";
import { createStats } from "./stats.js";
import { createCustomize } from "./customize.js";
import { createGeneFilter } from "./geneFilter.js";
import { BINS, darken, idOf, nodeVisible, visibleEdges } from "./logic.js";
import { buildColorModes } from "./colorModes.js";
import { exportPng, exportSvg, exportTsv } from "./export.js";
import { lassoIcon } from "./lasso.js";

const fmt = (x) => x.toFixed(2);
export const DEFAULT_THRESHOLD = 0.6; // only edges above this score are shown when the graph opens

/** The network-graph page of one list. */
export function createGraphView({
  api,
  listId,
  listName,
  colors,
  annotationId = "",
  taxonName = "",
  onBack,
}) {
  const st = {
    data: null,
    loading: true,
    error: "",
    experiments: [],
    expIds: [],
    threshold: DEFAULT_THRESHOLD,
    geneFilter: "all",
    colors,
    seq: 0,
    expOpen: false,
    exportOpen: false,
    lasso: false,
  };
  const disposers = [];
  let geneIds = null; // the genes in the graph (null: the whole list): shrinks when genes are deleted

  // ---------- skeleton ----------
  const tooltip = h("div", { class: "tooltip", hidden: true });
  const host = h("div", { class: "graph-host" });
  const loadingEl = h("div", { class: "graph-overlay" });
  const emptyEl = h("div", { class: "graph-empty", hidden: true });
  const filterVal = h("span", { class: "filter-val" }, fmt(DEFAULT_THRESHOLD));
  const filter = h("input", {
    type: "range",
    min: "0",
    max: "1",
    step: "0.01",
    value: String(DEFAULT_THRESHOLD),
    class: "filter-range",
    "aria-label": "Minimum edge score",
    oninput: (e) => {
      st.threshold = +e.target.value;
      filterVal.textContent = fmt(st.threshold);
      scheduleRefresh();
    },
  });
  const zoomPct = h("span", { class: "zoom-pct" }, "100%");
  const zoomRange = h("input", {
    type: "range",
    class: "zoom-range",
    min: "-300",
    max: "300",
    step: "1",
    value: "0",
    title: "Zoom (scroll or pinch also works)",
    "aria-label": "Zoom",
    oninput: (e) => graph.zoomTo(2 ** (+e.target.value / 100)),
  });
  const geneFilter = createGeneFilter({
    onChange: (f) => {
      st.geneFilter = f;
      scheduleRefresh();
    },
  });
  const lassoBtn = h(
    "button",
    {
      class: "lasso-btn",
      title:
        "Multiple selection: draw an outline around the genes you want to select",
      "aria-label": "Multiple selection",
      "aria-pressed": "false",
      onclick: () => toggleLasso(),
    },
    lassoIcon(),
    h("span", {}, "Multiple selection")
  );
  const positionResetBtn = h(
    "button",
    {
      class: "position-reset-btn",
      title: "Move every gene back to its original position",
      onclick: () => {
        hideMenu();
        stats.setSelected(null);
        graph.resetPositions();
      },
    },
    "Position reset"
  );
  const customizeBtn = h(
    "button",
    {
      class: "customize-btn",
      title: "Customize the colours of nodes and edges",
      onclick: () => customize.toggle(),
    },
    "Customize"
  );

  const graph = createGraph(host, {
    tooltip,
    onSelect(ids) {
      hideMenu();
      if (ids.length) stats.setSelected(null);
    }, // a clicked gene replaces the one located via the statistics box
    onLasso: ({ ids, at, cancelled }) => {
      setLasso(false);
      if (cancelled) return;
      ids.length ? showMenu(at) : toast("No visible genes inside the outline.");
    },
    onMoved: ({ at }) => showMenu(at),
    onZoom(k) {
      zoomPct.textContent = `${Math.round(k * 100)}%`;
      zoomRange.value = String(Math.round(Math.log2(k) * 100));
    },
  });
  const stats = createStats({
    onSelect: (id) => (id ? graph.highlight(id) : graph.clearHighlight()),
  });
  const legendEl = h("div", { class: "legend" });
  const modes = buildColorModes(st.colors, listName);
  const customize = createCustomize({
    getModes: modes.getModes,
    getItems: modes.getItems,
    onChange: () => {
      graph.setColors(st.colors);
      renderLegend();
    },
    ignoreOutside: [customizeBtn],
  });

  const tagsEl = h("div", { class: "tags" });
  const expBtn = h("button", {
    class: "select-btn",
    "aria-haspopup": "listbox",
    title: "Choose one or more expression experiments",
    onclick: () => {
      st.expOpen = !st.expOpen;
      renderExp();
    },
  });
  const expList = h("div", {
    class: "popover exp-list",
    role: "listbox",
    "aria-multiselectable": "true",
    hidden: true,
  });
  const expDesc = h("div", { class: "exp-desc" });
  const exportBtn = h(
    "button",
    {
      class: "export-btn",
      title: "Export the graph",
      onclick: () => {
        st.exportOpen = !st.exportOpen;
        renderExport();
      },
    },
    "Export ▾"
  );
  const exportMenu = h("div", { class: "popover export-menu", hidden: true });
  const toastEl = h("div", {
    class: "graph-toast",
    hidden: true,
    role: "status",
  });
  const menuEl = h("div", { class: "lasso-menu", role: "menu", hidden: true });
  const dialogEl = h("div", { class: "overlay", hidden: true });

  const area = h(
    "div",
    { class: "graph-area" },
    host,
    tooltip,
    h(
      "div",
      { class: "graph-tools-top" },
      geneFilter.el,
      lassoBtn,
      positionResetBtn
    ),
    h(
      "div",
      {
        class: "score-filter",
        title: "Only edges with a score greater than this value are shown",
      },
      h("div", { class: "filter-title" }, "Score filter ", filterVal),
      h(
        "div",
        { class: "filter-box" },
        h("span", {}, "0"),
        filter,
        h("span", {}, "1")
      )
    ),
    emptyEl,
    loadingEl,
    toastEl,
    menuEl,
    h(
      "div",
      { class: "graph-tools" },
      customizeBtn,
      h(
        "div",
        { class: "zoom-box" },
        h(
          "button",
          {
            class: "reset-btn",
            title: "Reset the view to fit the whole graph",
            onclick: () => graph.reset(),
          },
          "Reset"
        ),
        h(
          "div",
          { class: "zoom-row" },
          h(
            "button",
            {
              class: "zbtn",
              title: "Zoom out",
              "aria-label": "Zoom out",
              onclick: () => graph.zoomBy(1 / 1.4),
            },
            "−"
          ),
          zoomRange,
          h(
            "button",
            {
              class: "zbtn",
              title: "Zoom in",
              "aria-label": "Zoom in",
              onclick: () => graph.zoomBy(1.4),
            },
            "+"
          )
        ),
        zoomPct
      )
    ),
    h(
      "div",
      { class: "graph-hint" },
      "Scroll or pinch to zoom · drag to pan · click a gene to select it (Ctrl+click: several, Delete: remove) · drag a gene to move it"
    )
  );

  const el = h(
    "div",
    { class: "graph-page" },
    h(
      "nav",
      { class: "breadcrumb" },
      "Lists › ",
      h(
        "button",
        { class: "link", onclick: onBack, title: "Back to the list page" },
        listName
      ),
      " › Network graph"
    ),
    h(
      "section",
      { class: "card header-card" },
      h(
        "div",
        { class: "header-left" },
        h("h1", {}, listName),
        h("div", { class: "subtitle" }, "Network graph"),
        tagsEl
      ),
      h(
        "div",
        { class: "header-mid" },
        h("div", { class: "field-label" }, "Expression experiment"),
        h("div", { class: "select-wrap" }, expBtn, expList),
        expDesc
      ),
      h(
        "div",
        { class: "header-right" },
        h("div", { class: "select-wrap" }, exportBtn, exportMenu)
      )
    ),
    h(
      "section",
      { class: "card graph-card" },
      area,
      h("aside", { class: "graph-side" }, legendEl, stats.el),
      customize.el
    ),
    dialogEl
  );

  // ---------- rendering ----------
  function renderTags() {
    clear(tagsEl);
    const nGenes = st.data?.nodes.length;
    append(tagsEl, [
      taxonName && h("span", { class: "tag" }, taxonName),
      nGenes != null && h("span", { class: "tag" }, `${nGenes} genes`),
    ]); // (append skips the false; Element.append would print it)
  }

  function renderLegend() {
    clear(legendEl);
    if (!st.data) return;
    const c = st.colors;
    legendEl.append(
      h(
        "div",
        { class: "legend-lists" },
        h(
          "div",
          { class: "legend-item" },
          h("span", {
            class: "dot",
            style: { background: c.node, borderColor: darken(c.node) },
          }),
          h("span", { class: "legend-name" }, listName)
        )
      ),
      h(
        "div",
        {
          class: "edge-legend",
          title:
            "Lines connect genes by expression score in the selected experiments",
        },
        h("div", { class: "edge-legend-title" }, "Expression score"),
        BINS.map((b) =>
          h(
            "div",
            { class: "edge-legend-row" },
            lineSample(c.edge, b.width, 27, b.opacity),
            h("span", {}, `${fmt(b.min)}–${fmt(b.max)}`)
          )
        )
      )
    );
  }

  function renderExp() {
    expBtn.textContent = "";
    expBtn.append(
      h(
        "span",
        { class: "select-text" },
        st.expIds.length === 0
          ? "Choose an expression experiment"
          : st.expIds.length === 1
            ? st.expIds[0]
            : `${st.expIds.length} experiments selected`
      ),
      h("span", { class: "caret" }, "▾")
    );
    expBtn.setAttribute("aria-expanded", String(st.expOpen));
    expList.hidden = !st.expOpen;
    clear(expList);
    expList.append(
      ...st.experiments.map((x) =>
        h(
          "label",
          {
            class: "exp-item",
            title: x.description || x.name,
            role: "option",
            "aria-selected": String(st.expIds.includes(x.id)),
          },
          h("input", {
            type: "checkbox",
            checked: st.expIds.includes(x.id),
            onchange: () => toggleExperiment(x.id),
          }),
          x.name
        )
      )
    );
    expDesc.textContent = st.expIds.length
      ? `Edges: expression in ${st.expIds.join(", ")}`
      : "Select one or more experiments to add expression edges";
  }
  function renderExport() {
    exportMenu.hidden = !st.exportOpen;
    clear(exportMenu);
    const item = (label, fn, tip) =>
      h(
        "button",
        {
          class: "menu-item",
          title: tip,
          onclick: () => {
            st.exportOpen = false;
            renderExport();
            fn();
          },
        },
        label
      );
    const vis = () => {
      const v = st.data.nodes.filter((n) => nodeVisible(n, st.geneFilter));
      return [v, shownEdges()];
    };
    exportMenu.append(
      item(
        "PNG image",
        () => exportPng(graph.toSvgString(), graph.size(), "network-graph"),
        "Download the current view as a PNG image"
      ),
      item(
        "SVG image",
        () => exportSvg(graph.toSvgString(), "network-graph"),
        "Download the current view as a vector SVG"
      ),
      item(
        "TSV matrix",
        () => exportTsv(...vis(), "network-graph"),
        "Download the visible genes and their edge scores as a matrix"
      )
    );
    exportBtn.disabled = !st.data;
  }

  function renderStatus() {
    loadingEl.hidden = !(st.loading || st.error);
    clear(loadingEl);
    loadingEl.append(
      st.error
        ? h(
            "div",
            { class: "error" },
            st.error,
            " ",
            h("button", { class: "link", onclick: () => load() }, "Retry")
          )
        : h("div", { class: "spinner-text" }, "Building graph…")
    );
  }

  const shownEdges = () =>
    st.data
      ? visibleEdges(st.data.nodes, st.data.edges, st.threshold, st.geneFilter)
      : [];

  let refreshQueued = false;
  const scheduleRefresh = () => {
    if (!refreshQueued) {
      refreshQueued = true;
      requestAnimationFrame(() => {
        refreshQueued = false;
        refresh();
      });
    }
  };

  /** threshold / annotation filter changes: update the graph, the stats box and the hints. */
  function refresh() {
    if (!st.data) return;
    graph.setThreshold(st.threshold);
    graph.setGeneFilter(st.geneFilter);
    const edges = shownEdges();
    stats.update(edges);
    emptyEl.hidden = st.loading || edges.length > 0;
    emptyEl.classList.toggle("prompt", st.expIds.length === 0);
    emptyEl.textContent =
      st.expIds.length === 0
        ? "Select an experiment to import data"
        : st.data.edges.length === 0
          ? "No expression edges: the genes of this list are not measured in the selected experiment(s)."
          : st.geneFilter !== "all"
            ? "No edges between the genes the annotation filter lets through."
            : "No edges above the current score filter.";
  }

  // ---------- messages ----------
  let toastTimer;
  const toast = (text) => {
    toastEl.textContent = text;
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.hidden = true;
    }, 3500);
  };
  let asking = false;
  let menuAt = null;

  // ---------- multiple selection ----------
  function setLasso(on) {
    st.lasso = on;
    lassoBtn.classList.toggle("active", on);
    lassoBtn.setAttribute("aria-pressed", String(on));
    on ? graph.startLasso() : graph.stopLasso();
  }
  function toggleLasso() {
    hideDialog();
    setLasso(!st.lasso);
    if (st.lasso) {
      hideMenu();
      toast("Draw an outline around the genes to select. Esc cancels.");
    }
  }

  /** The box with what can be done with the selected genes, next to where the outline was closed. */
  function showMenu(at) {
    menuAt = at;
    const ids = graph.selectedIds();
    if (!ids.length) return hideMenu();
    clear(menuEl);
    const act = (label, fn, tip) =>
      h(
        "button",
        {
          class: "menu-item",
          role: "menuitem",
          title: tip,
          onclick: () => {
            hideMenu();
            fn();
          },
        },
        label
      );
    menuEl.append(
      h(
        "div",
        { class: "lasso-menu-title" },
        `${ids.length} ${ids.length === 1 ? "gene" : "genes"} selected`
      ),
      act(
        "Export to a new list",
        () => showExportDialog(ids),
        "Save the selected genes as a new gene list"
      ),
      act(
        "Delete",
        () => deleteSelected(),
        "Remove the selected genes from the graph"
      ),
      act(
        "Inspect",
        () => showInspectDialog(ids),
        "Show the IDs, descriptions and species of the selected genes"
      )
    );
    menuEl.hidden = false;
    const box = area.getBoundingClientRect();
    menuEl.style.left = `${Math.max(8, Math.min(at[0] + 12, box.width - menuEl.offsetWidth - 8))}px`;
    menuEl.style.top = `${Math.max(8, Math.min(at[1] + 12, box.height - menuEl.offsetHeight - 8))}px`;
  }
  const hideMenu = () => {
    menuEl.hidden = true;
  };

  function hideDialog() {
    dialogEl.hidden = true;
    clear(dialogEl);
  }
  function closeDialog() {
    hideDialog();
    if (menuAt) showMenu(menuAt);
  }
  function openDialog(card, label) {
    clear(dialogEl);
    dialogEl.setAttribute("role", "dialog");
    dialogEl.setAttribute("aria-modal", "true");
    dialogEl.setAttribute("aria-label", label);
    dialogEl.append(card);
    dialogEl.hidden = false;
    dialogEl.onpointerdown = (e) => {
      if (e.target === dialogEl) closeDialog();
    };
  }

  function showInspectDialog(ids) {
    const rows = graph.nodesById(ids).sort((a, b) => a.id.localeCompare(b.id));
    openDialog(
      h(
        "div",
        { class: "card ng-dialog inspect-dialog" },
        h(
          "h2",
          { class: "dialog-title" },
          "Information about the selected genes"
        ),
        h(
          "div",
          { class: "inspect-table", role: "table" },
          h(
            "div",
            { class: "inspect-row inspect-head", role: "row" },
            h("span", {}, "Gene ID"),
            h("span", {}, "Description"),
            h("span", {}, "Species")
          ),
          h(
            "div",
            { class: "inspect-rows" },
            rows.map((n) =>
              h(
                "div",
                { class: "inspect-row", role: "row" },
                h("span", { class: "gene-id" }, n.id),
                h(
                  "span",
                  { class: "inspect-desc", title: n.description || "" },
                  n.description || "No description"
                ),
                h("span", {}, taxonName)
              )
            )
          )
        ),
        h(
          "div",
          { class: "dialog-actions" },
          h("button", { class: "pill primary", onclick: closeDialog }, "Close")
        )
      ),
      "Information about the selected genes"
    );
  }

  function showExportDialog(ids) {
    const name = h("input", {
      class: "input",
      type: "text",
      maxlength: "200",
      "aria-label": "List name",
      placeholder: "List name",
      value: `${listName} – selection`,
    });
    const description = h("textarea", {
      class: "input",
      rows: "3",
      "aria-label": "Description (optional)",
      placeholder: "Description (optional)",
    });
    const msg = h("div", { class: "error", hidden: true });
    const create = h(
      "button",
      { class: "pill primary", onclick: submit },
      "Create list"
    );
    async function submit() {
      const title = name.value.trim();
      if (!title) {
        msg.textContent = "Give the list a name.";
        msg.hidden = false;
        return name.focus();
      }
      create.disabled = true;
      msg.hidden = true;
      try {
        await api.exportList({
          name: title,
          description: description.value.trim(),
          annotationId,
          taxonName,
          geneIds: ids,
        });
        closeDialog();
        toast(
          `List “${title}” created with ${ids.length} ${ids.length === 1 ? "gene" : "genes"}.`
        );
      } catch (e) {
        msg.textContent = e.message;
        msg.hidden = false;
        create.disabled = false;
      }
    }
    openDialog(
      h(
        "div",
        { class: "card ng-dialog export-dialog" },
        h("h2", { class: "dialog-title" }, "Export to a new list"),
        h(
          "p",
          { class: "dialog-text" },
          `${ids.length} ${ids.length === 1 ? "gene" : "genes"} will be saved as a new list.`
        ),
        h("label", { class: "field-label" }, "Title"),
        name,
        h("label", { class: "field-label" }, "Description"),
        description,
        msg,
        h(
          "div",
          { class: "dialog-actions" },
          h("button", { class: "pill", onclick: closeDialog }, "Cancel"),
          create
        )
      ),
      "Export to a new list"
    );
    name.focus();
    name.select();
    name.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submit();
    });
  }

  // ---------- deleting genes ----------
  /** Delete the selected genes (Delete key, or the multiple selection's menu): out of the graph. */
  async function deleteSelected() {
    const ids = graph.selectedIds();
    if (!ids.length || !st.data || st.loading || asking) return;
    if (ids.length >= st.data.nodes.length)
      return toast(
        "A graph needs at least one gene – select fewer genes to delete."
      );
    if (!deleteConfirmSkipped()) {
      asking = true;
      const ok = await confirmDeleteGenes(
        ids,
        el.closest(".ng-root") ?? document.body
      );
      asking = false;
      if (!ok || !st.data) return;
    }
    const gone = new Set(ids);
    st.data = {
      ...st.data,
      nodes: st.data.nodes.filter((n) => !gone.has(n.id)),
      edges: st.data.edges.filter(
        (e) => !gone.has(idOf(e.source)) && !gone.has(idOf(e.target))
      ),
    };
    geneIds = st.data.nodes.map((n) => n.id);
    graph.removeNodes(ids);
    stats.setSelected(null);
    renderTags();
    refresh();
  }

  // ---------- data ----------
  let debounce;
  function toggleExperiment(id) {
    st.expIds = st.expIds.includes(id)
      ? st.expIds.filter((x) => x !== id)
      : [...st.expIds, id];
    renderExp(); // the list stays open so several experiments can be picked
    clearTimeout(debounce);
    debounce = setTimeout(() => load(), 250);
  }

  async function load() {
    const seq = ++st.seq;
    st.loading = true;
    st.error = "";
    renderStatus();
    try {
      const data = await api.graph({
        listId,
        geneIds,
        experimentIds: st.expIds,
      });
      if (seq !== st.seq) return; // a newer request superseded this one
      st.data = data;
      graph.setColors(st.colors);
      graph.setData(data.nodes, data.edges); // resets the layout, pins and view
      graph.setThreshold(st.threshold);
      stats.setSelected(null);
      renderTags();
      renderLegend();
      renderExport();
    } catch (e) {
      if (seq !== st.seq) return;
      st.error = e.message;
    }
    st.loading = false;
    renderStatus();
    refresh();
  }

  // ---------- init ----------
  // a gene is highlighted only through the statistics box; any click elsewhere makes it neutral again
  disposers.push(
    onOutsideClick([stats.el], () => {
      stats.setSelected(null);
      graph.clearHighlight();
    })
  );
  disposers.push(
    onOutsideClick([expBtn, expList], () => {
      if (st.expOpen) {
        st.expOpen = false;
        renderExp();
      }
    })
  );
  disposers.push(
    onOutsideClick([exportBtn, exportMenu], () => {
      if (st.exportOpen) {
        st.exportOpen = false;
        renderExport();
      }
    })
  );
  const onDelete = (e) => {
    if (
      (e.key !== "Delete" && e.key !== "Backspace") ||
      e.target.closest?.("input,textarea,select,[contenteditable]")
    )
      return;
    if (!graph.selectedIds().length) return;
    e.preventDefault();
    deleteSelected();
  };
  document.addEventListener("keydown", onDelete);
  disposers.push(() => document.removeEventListener("keydown", onDelete));
  const onKey = (e) => {
    if (e.key !== "Escape") return;
    st.expOpen = st.exportOpen = false;
    renderExp();
    renderExport();
    customize.close();
    if (st.lasso) setLasso(false);
    hideMenu();
    hideDialog();
  };
  document.addEventListener("keydown", onKey);
  renderTags();
  renderExp();
  renderExport();
  renderStatus();
  api
    .experiments(annotationId)
    .then((x) => {
      st.experiments = x;
      renderExp();
    })
    .catch((e) => {
      st.error = e.message;
      renderStatus();
    });
  load();

  return {
    el,
    destroy() {
      clearTimeout(debounce);
      clearTimeout(toastTimer);
      st.seq++;
      disposers.forEach((d) => d());
      document.removeEventListener("keydown", onKey);
      stats.destroy();
      graph.destroy();
      el.remove();
    },
  };
}
export { ZOOM_RANGE };
