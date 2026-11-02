const SVG_NS = "http://www.w3.org/2000/svg";

/** The multiple-selection icon: a dashed loop with a rope, like a lasso. */
export function lassoIcon(size = 16) {
  const svg = document.createElementNS(SVG_NS, "svg");
  for (const [k, v] of Object.entries({
    viewBox: "0 0 24 24",
    width: size,
    height: size,
    "aria-hidden": "true",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": 1.8,
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  }))
    svg.setAttribute(k, v);
  const loop = document.createElementNS(SVG_NS, "ellipse");
  for (const [k, v] of Object.entries({
    cx: 12,
    cy: 9,
    rx: 8.5,
    ry: 5.5,
    "stroke-dasharray": "3.2 2.6",
  }))
    loop.setAttribute(k, v);
  const rope = document.createElementNS(SVG_NS, "path");
  rope.setAttribute("d", "M7.2 13.6c-1.4 1.9-1.2 4.1.8 4.8 1.9.7 3.4-.5 3-2");
  svg.append(loop, rope);
  return svg;
}
