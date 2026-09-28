const LOW_COLOR = [243, 248, 245];
const HIGH_COLOR = [9, 126, 53];
const NO_DATA_COLOR = "rgb(245, 247, 250)";

export function colorFor(
  value: number | null,
  lowest: number,
  highest: number
): string {
  if (value === null) return NO_DATA_COLOR;
  const span = highest - lowest;
  const position = span === 0 ? 0 : (value - lowest) / span;
  const channels = LOW_COLOR.map((low, index) =>
    Math.round(low + (HIGH_COLOR[index] - low) * position)
  );
  return `rgb(${channels.join(", ")})`;
}
