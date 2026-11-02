/**
 * What the customize box can colour: the genes of the list and the edges. colors = { node, edge } is mutated in place.
 */
export function buildColorModes(colors, listName) {
  const items = {
    nodes: [
      {
        key: "genes",
        label: listName,
        get: () => colors.node,
        set: (c) => {
          colors.node = c;
        },
      },
    ],
    edges: [
      {
        key: "expression",
        label: "expression",
        get: () => colors.edge,
        set: (c) => {
          colors.edge = c;
        },
      },
    ],
  };
  return {
    getModes: () => [
      { id: "nodes", label: "nodes" },
      { id: "edges", label: "edges" },
    ],
    getItems: (id) => items[id],
  };
}
