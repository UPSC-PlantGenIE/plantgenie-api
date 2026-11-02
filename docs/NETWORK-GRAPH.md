# Network graph

The **Network graph** button on a list page opens the graph of that list at
once: genes are nodes, edges join genes whose expression moves together in an
experiment.

- **Expression score**: Pearson correlation of two genes' rows in the heatmap
  matrix of the chosen experiment(s); negative correlations give no edge, the
  best score over several experiments wins. Edges are black.

The graph opens without edges: pick an experiment in the header ("Select an
experiment to import data" is shown until then). The dropdown offers the
experiments of the list's annotation, the same ones the heatmap offers. Only
edges above **0.6** are drawn at first; the score filter at the top goes down
to 0.

## How it connects to the rest of plantgenie

| Network graph needs | Comes from |
|---|---|
| the list | `gene_lists` / `gene_list_members` in SQLite, per account (same as `/v2/lists`) |
| gene descriptions | `Gene.description` in Neo4j, looked up on the list's annotation |
| experiments | `GET /v2/annotations/{id}/experiments`, as for the heatmap |
| expression values | `Gene-[:EXPRESSED_IN {value}]->Sample` ordered by `Sample.order`, as in `/v2/experiments/{id}/expression` |
| login | the `Authorization: Bearer <account id>` header every `/v2/lists` call uses |
| exporting genes as a list | `POST /v2/lists`, then `PATCH /v2/lists/{id}` with `addGeneIds` |

## On the graph page

- **Annotation filter** (top left, a bar with three stops): middle = show all
  genes (default); left = only uncharacterized genes; right = hide genes
  without annotations. "Uncharacterized" means the gene has no description
  in Neo4j. The edges, statistics and the multiple selection follow the filter:
  hidden genes are never selected.
- **Selecting a gene**: the genes connected to it (by visible edges) gather
  around it and shine, and every other gene is shoved back. Unselecting
  glides everything back. Timings are the constants at the top of `graph.js`;
  the push itself is `pushBack` in `focus.js`.
- **Dragging**: a single gene pulls the genes connected to it (two steps out)
  along, "sticky" like in Neo4j: they trail behind and settle after the drop
  (`PULL_*` constants in `graph.js`). Several selected genes (Ctrl+click or
  the multiple selection) move together as a frozen shape and pull nothing.
- **Multiple selection** (lasso button, top left): draw a dashed outline around
  genes; a menu offers *Export to a new list* (title, optional description),
  *Delete* and *Inspect* (gene ID, description and species). The genes that
  were gathered around a selected gene stay close while selecting. Esc
  cancels.
- **Customize**: one colour for the genes and one for the edges, from a
  palette or the colour picker.
- The legend and the statistics box have the rounded corners of the app's
  cards (12px). The graph frame fills the window below the header; the
  Customize box opens over the frame.

## Code

Backend `src/plantgenie_api/api/v2/network/`

- `routes.py` - the endpoint, Neo4j/SQLite access (async)
- `graph.py` - builds nodes and edges from the data the route fetched (pure)
- `coexpression.py` - Pearson correlation and the pair search (numpy)
- `models.py` - request and response models

One endpoint, `POST /v2/network-graph/graph`, which needs an account:

```json
{ "listId": "...", "geneIds": ["..."], "experimentIds": ["..."] }
```

`geneIds` is optional (default: every gene of the list); the page sends it
after genes are deleted from the graph. The response is
`{ "nodes": [{ "id", "description" }], "edges": [{ "source", "target", "score" }] }`.
An experiment of another annotation, or a selection without genes, is a 422;
another account's list is a 404.

Every possible edge is returned. Selections that would produce more than
`NETWORK_GRAPH_MAX_EDGES` (default 100000) are refused with a message.

Frontend `ui/src/networkGraph/` (plain JS + d3) and
`ui/src/components/network/NetworkGraph.tsx`, which mounts it from the list
page's "Network graph" button. The graph page covers the viewport
(`.ng-root.has-graph`); the stylesheet is nested under `.ng-root`.

## Tests

- Backend: `src/tests/plantgenie_api/unit/test_network_graph.py`
- Frontend: `ui/src/networkGraph/test/*.test.js` (logic, gestures,
  `graphView.test.js` for the page, and `graphInteraction.test.js` for the
  multiple selection and the drag), `ui/src/components/network/NetworkGraph.test.tsx`,
  and the "network graph" case in `ListPage.test.tsx`

## Known limits

- Expression values are matched by gene id, as for the heatmap: a gene id
  that exists under two annotations is treated as one gene.
- Not yet looked at in a browser: the feel of the sticky drag and the lasso
  on a touch screen (everything is unit-tested).
