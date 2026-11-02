// The first palette is the default one. Colours are listed row by row, as the swatches sit in the palette card
// (three per row), so a palette looks in the customize box as it does in the design.
export const PALETTES = [
  {
    id: "viz-gold",
    name: "Viz Gold",
    colors: [
      "#0300FC",
      "#9E00D7",
      "#CE34B6",
      "#FDD803",
      "#FC8772",
      "#EA6095",
      "#FEB34F",
    ],
  },
  {
    id: "vivid-light",
    name: "Vivid light",
    colors: [
      "#FD6D6D",
      "#FFFF29",
      "#6DC6FD",
      "#FD6DAB",
      "#02FEFE",
      "#E06DFD",
      "#6DFD9D",
      "#FFBF7E",
    ],
  },
  {
    id: "faded-light",
    name: "Faded light",
    colors: [
      "#BEAED4",
      "#D5A6C8",
      "#FBBED3",
      "#FF9E9A",
      "#6DE7FD",
      "#ECA0B2",
      "#8DD17D",
      "#FDF16D",
      "#FDBA6D",
      "#489994",
      "#984EA3",
      "#D37295",
    ],
  },
  {
    id: "solid",
    name: "Solid",
    colors: [
      "#FF7F00",
      "#E4211C",
      "#984EA3",
      "#A65629",
      "#4DAF4A",
      "#E72A8A",
      "#F781BF",
      "#377EB8",
      "#EFDC60",
    ],
  },
  {
    id: "paired",
    name: "Paired",
    colors: [
      "#FDCDAC",
      "#B3E2CD",
      "#FEA090",
      "#FC8D62",
      "#66C2A5",
      "#D02155",
      "#A2CCF6",
      "#CBD5E8",
      "#F4CAE4",
      "#2AA1ED",
      "#8DA0CB",
      "#E78AC3",
    ],
  },
  {
    id: "dark",
    name: "Dark",
    colors: [
      "#771434",
      "#F28E2A",
      "#79706E",
      "#864724",
      "#02722D",
      "#7D2D8F",
      "#324476",
    ],
  },
  {
    id: "neon",
    name: "Neon",
    colors: [
      "#02FF00",
      "#FF01FF",
      "#FF0000",
      "#0300FC",
      "#FFFF12",
      "#9A00FF",
      "#FF6A00",
    ],
  },
];

// Edge colour: black (not a Viz Gold colour, the default palette, so an edge never looks like it belongs to a group of genes).
export const DEFAULT_EDGE_COLOR = "#000000";

/** A random colour of the default palette for the genes. */
export function randomNodeColor(rng = Math.random) {
  const colors = PALETTES[0].colors;
  return colors[Math.floor(rng() * colors.length)];
}
