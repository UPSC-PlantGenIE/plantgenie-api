export const MINIMUM_CELL_WIDTH = 8;
export const MAXIMUM_CELL_WIDTH = 48;

export function cellWidthFor(
  availableWidth: number,
  sampleCount: number,
  labelWidth: number
): number {
  if (availableWidth <= 0 || sampleCount <= 0) return MAXIMUM_CELL_WIDTH;
  const perSample = (availableWidth - labelWidth) / sampleCount;
  return Math.min(
    MAXIMUM_CELL_WIDTH,
    Math.max(MINIMUM_CELL_WIDTH, perSample)
  );
}
