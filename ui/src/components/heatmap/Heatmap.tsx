import { useEffect, useRef, useState } from "react";
import type { ExpressionSample } from "../../api/plantgenieApi";
import { colorFor } from "./colorFor";
import { cellWidthFor } from "./cellWidthFor";

interface HeatmapProps {
  genes: string[];
  samples: ExpressionSample[];
  values: (number | null)[][];
  showLabels?: boolean;
  onCellHover?: (gene: string, sample: string, value: number | null) => void;
}

const CELL_HEIGHT = 22;
const MINIMUM_LABEL_WIDTH = 150;
const GENE_LABEL_FONT_SIZE = 12;
const SAMPLE_LABEL_FONT_SIZE = 10;
const LABEL_CHARACTER_WIDTH = GENE_LABEL_FONT_SIZE * 0.62;
const LABEL_HEIGHT = 90;

export default function Heatmap({
  genes,
  samples,
  values,
  showLabels = true,
  onCellHover,
}: HeatmapProps) {
  const present = values.flat().filter((v): v is number => v !== null);
  const lowest = present.length > 0 ? Math.min(...present) : 0;
  const highest = present.length > 0 ? Math.max(...present) : 0;

  const longestGeneId = genes.reduce(
    (longest, gene) => Math.max(longest, gene.length),
    0
  );
  const labelWidth = showLabels
    ? Math.max(
        MINIMUM_LABEL_WIDTH,
        longestGeneId * LABEL_CHARACTER_WIDTH + 12
      )
    : 0;
  const labelHeight = showLabels ? LABEL_HEIGHT : 0;

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    const element = containerRef.current;
    if (!element || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      setContainerWidth(entries[0].contentRect.width);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const cellWidth = cellWidthFor(
    containerWidth,
    samples.length,
    labelWidth
  );

  const width = labelWidth + samples.length * cellWidth;
  const height = labelHeight + genes.length * CELL_HEIGHT;

  return (
    <div ref={containerRef}>
    <svg
      role="img"
      aria-label={`Expression heatmap, ${genes.length} genes by ${samples.length} samples`}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="h-auto max-w-full"
    >
      {showLabels &&
        samples.map((sample, column) => (
        <text
          key={sample.id}
          x={labelWidth + column * cellWidth + cellWidth / 2}
          y={labelHeight - 8}
          transform={`rotate(-90, ${
            labelWidth + column * cellWidth + cellWidth / 2
          }, ${labelHeight - 8})`}
          fontFamily="ui-sans-serif, system-ui, sans-serif"
          fontSize={SAMPLE_LABEL_FONT_SIZE}
          fill="#616980"
          textAnchor="start"
        >
          {sample.id}
        </text>
      ))}
      {genes.map((gene, row) => (
        <g key={gene}>
          {showLabels && (
            <text
              x={0}
              y={labelHeight + row * CELL_HEIGHT + CELL_HEIGHT / 2 + 4}
              fontFamily="ui-sans-serif, system-ui, sans-serif"
              fontSize={GENE_LABEL_FONT_SIZE}
              fontWeight={600}
              fill="#3885f5"
            >
              {gene}
            </text>
          )}
          {samples.map((sample, column) => {
            const value = values[row]?.[column] ?? null;
            return (
              <rect
                key={sample.id}
                data-cell={`${gene}:${sample.id}`}
                x={labelWidth + column * cellWidth}
                y={labelHeight + row * CELL_HEIGHT}
                width={cellWidth - 1}
                height={CELL_HEIGHT - 1}
                fill={colorFor(value, lowest, highest)}
                onMouseEnter={() => onCellHover?.(gene, sample.id, value)}
              >
                <title>{`${gene} · ${sample.id} · ${value ?? "no data"}`}</title>
              </rect>
            );
          })}
        </g>
      ))}
    </svg>
    </div>
  );
}
