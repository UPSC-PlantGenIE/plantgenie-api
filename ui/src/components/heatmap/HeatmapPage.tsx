import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "wouter";
import {
  useGetExperimentsQuery,
  useGetExpressionQuery,
  useGetListQuery,
} from "../../api/plantgenieApi";
import Heatmap from "./Heatmap";

const storageKey = (annotationId: string) =>
  `heatmap-experiment-${annotationId}`;

const readRemembered = (annotationId: string): string | null => {
  try {
    return localStorage.getItem(storageKey(annotationId));
  } catch {
    return null;
  }
};

const remember = (annotationId: string, experimentId: string) => {
  try {
    localStorage.setItem(storageKey(annotationId), experimentId);
  } catch {
    // a viewer with blocked storage still gets a working heatmap
  }
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

const LABELS_MEDIA_QUERY = "(min-width: 640px)";

const useHasRoomForLabels = () => {
  const [hasRoom, setHasRoom] = useState(
    () => window.matchMedia?.(LABELS_MEDIA_QUERY).matches ?? true
  );

  useEffect(() => {
    const query = window.matchMedia?.(LABELS_MEDIA_QUERY);
    if (!query) return;
    const handleChange = (event: MediaQueryListEvent) =>
      setHasRoom(event.matches);
    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);

  return hasRoom;
};

const slugify = (name: string) =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

export default function HeatmapPage() {
  const { listId } = useParams<{ listId: string }>();
  const { data: list } = useGetListQuery(listId ?? "", { skip: !listId });
  const annotationId = list?.annotationId ?? "";
  const { data: experiments } = useGetExperimentsQuery(annotationId, {
    skip: !annotationId,
  });
  const [chosenExperimentId, setChosenExperimentId] = useState<string | null>(
    null
  );

  const defaultExperiment =
    experiments && experiments.length > 0
      ? (experiments.find((e) => e.id === readRemembered(annotationId)) ??
        experiments[0])
      : null;
  const experimentId = chosenExperimentId ?? defaultExperiment?.id ?? null;

  useEffect(() => {
    if (annotationId && experimentId) remember(annotationId, experimentId);
  }, [annotationId, experimentId]);

  const { data: expression, isFetching } = useGetExpressionQuery(
    {
      experimentId: experimentId ?? "",
      geneIds: list?.memberGeneIds ?? [],
    },
    { skip: !experimentId || (list?.memberGeneIds.length ?? 0) === 0 }
  );

  const experiment = experiments?.find((e) => e.id === experimentId);
  const heatmapRef = useRef<HTMLDivElement>(null);
  const hasRoomForLabels = useHasRoomForLabels();
  const [isExportOpen, setIsExportOpen] = useState(false);

  const exportBaseName = `${slugify(list?.name ?? "heatmap")}-${
    experimentId ?? "experiment"
  }`;

  const handleExportTsv = () => {
    if (!expression) return;
    const header = ["geneId", ...expression.samples.map((s) => s.id)];
    const rows = expression.geneIds.map((geneId, row) =>
      [
        geneId,
        ...expression.values[row].map((value) =>
          value === null ? "" : String(value)
        ),
      ].join("\t")
    );
    downloadBlob(
      new Blob([[header.join("\t"), ...rows].join("\n")], {
        type: "text/tab-separated-values",
      }),
      `${exportBaseName}.tsv`
    );
    setIsExportOpen(false);
  };

  const handleExportSvg = () => {
    const svg = heatmapRef.current?.querySelector("svg");
    if (!svg) return;
    const markup = new XMLSerializer().serializeToString(svg);
    downloadBlob(
      new Blob([markup], { type: "image/svg+xml" }),
      `${exportBaseName}.svg`
    );
    setIsExportOpen(false);
  };

  const handleExportPng = () => {
    const svg = heatmapRef.current?.querySelector("svg");
    if (!svg) return;
    const markup = new XMLSerializer().serializeToString(svg);
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = Number(svg.getAttribute("width")) || image.width;
      canvas.height = Number(svg.getAttribute("height")) || image.height;
      const context = canvas.getContext("2d");
      if (!context) return;
      context.fillStyle = "white";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) downloadBlob(blob, `${exportBaseName}.png`);
      });
    };
    image.src = `data:image/svg+xml;base64,${btoa(
      unescape(encodeURIComponent(markup))
    )}`;
    setIsExportOpen(false);
  };
  const scaled = expression
    ? expression.values.map((row) =>
        row.map((value) =>
          value === null || expression.unit !== "tpm"
            ? value
            : Math.log2(value + 1)
        )
      )
    : [];

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-8">
      <nav className="text-xs text-muted" aria-label="Breadcrumb">
        <Link href="/lists" className="hover:text-heading">
          My Lists
        </Link>
        <span className="px-2">/</span>
        <Link href={`/lists/${listId}`} className="hover:text-heading">
          {list?.name ?? "List"}
        </Link>
        <span className="px-2">/</span>
        <span>Heatmap</span>
      </nav>

      <article className="mt-6 rounded-xl border border-border bg-card px-6 py-5 shadow-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-xl font-bold text-heading">
              {list?.name ?? "Heatmap"}
            </h1>
            <p className="mt-1 text-sm text-muted">Expression heatmap</p>
          </div>
          <div className="shrink-0">
            <label
              htmlFor="experiment"
              className="block text-xs font-semibold text-muted"
            >
              Experiment
            </label>
            <select
              id="experiment"
              value={experimentId ?? ""}
              onChange={(event) => setChosenExperimentId(event.target.value)}
              className="mt-1 h-8 w-64 rounded-md border border-border bg-card px-2 text-xs font-medium text-heading"
            >
              {(experiments ?? []).map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </select>
            {experiment?.description && (
              <p className="mt-2 w-64 text-xs text-muted">
                {experiment.description}
              </p>
            )}
          </div>
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => setIsExportOpen((open) => !open)}
              disabled={!expression}
              aria-haspopup="menu"
              aria-expanded={isExportOpen}
              className="mt-5 inline-flex h-8 items-center justify-center rounded-md border border-border bg-card px-3 text-xs font-semibold text-label shadow-card disabled:cursor-not-allowed disabled:opacity-50"
            >
              Export ▾
            </button>
            {isExportOpen && (
              <div
                role="menu"
                className="absolute right-0 z-10 mt-1 w-36 rounded-md border border-border bg-card py-1 shadow-card"
              >
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleExportPng}
                  className="block w-full px-3 py-2 text-left text-xs font-medium text-heading hover:bg-surface"
                >
                  PNG image
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleExportSvg}
                  className="block w-full px-3 py-2 text-left text-xs font-medium text-heading hover:bg-surface"
                >
                  SVG image
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleExportTsv}
                  className="block w-full px-3 py-2 text-left text-xs font-medium text-heading hover:bg-surface"
                >
                  TSV matrix
                </button>
              </div>
            )}
          </div>
        </div>
      </article>

      {experiments && experiments.length === 0 && (
        <p className="mt-6 text-sm text-muted">
          No expression experiments for this genome yet.
        </p>
      )}

      {expression && (
        <section
          ref={heatmapRef}
          className="mt-6 overflow-x-auto rounded-xl border border-border bg-card px-6 py-5 shadow-card"
        >
          <Heatmap
            genes={expression.geneIds}
            samples={expression.samples}
            values={scaled}
            showLabels={hasRoomForLabels}
          />
          <p className="mt-4 text-xs text-muted">
            {expression.unit === "tpm" ? "log2(TPM + 1)" : expression.unit}
          </p>
        </section>
      )}

      {isFetching && !expression && (
        <div className="mt-6 h-64 animate-pulse rounded-xl bg-border/40" />
      )}

      {expression && expression.missingGeneIds.length > 0 && (
        <section className="mt-6 rounded-xl border border-border bg-surface px-6 py-4">
          <p className="text-sm font-semibold text-muted">
            {expression.missingGeneIds.length}{" "}
            {expression.missingGeneIds.length === 1 ? "gene has" : "genes have"}{" "}
            no data in this experiment
          </p>
          <p className="mt-2 flex flex-wrap gap-3 text-sm font-medium text-primary">
            {expression.missingGeneIds.map((geneId) => (
              <span key={geneId}>{geneId}</span>
            ))}
          </p>
        </section>
      )}
    </div>
  );
}
