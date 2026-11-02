import { createApi } from "./api.js";
import { createGraphView } from "./view.js";
import { DEFAULT_EDGE_COLOR, randomNodeColor } from "./palettes.js";
import "./networkGraph.css";

/**
 * Entry point for the list page.
 *
 *   const graph = openNetworkGraph({ host, apiRoot, getHeaders, listId, listName, annotationId, taxonName, onClose });
 *   graph.destroy();
 *
 * host         element the feature renders into (the graph page replaces its content)
 * apiRoot      URL of the v2 API (.../api/v2)
 * getHeaders   headers added to every request (the account's Authorization)
 * listId, listName, annotationId, taxonName   the list the user is looking at; a list exported from the graph
 *              gets the same annotation and taxon
 */
export function openNetworkGraph({
  host,
  apiRoot = "",
  getHeaders,
  listId,
  listName = "",
  annotationId = "",
  taxonName = "",
  onClose = () => {},
}) {
  let destroyed = false;
  const scope = document.createElement("div");
  scope.className = "ng-root has-graph";
  host.append(scope);
  const view = createGraphView({
    api: createApi(apiRoot, getHeaders),
    listId,
    listName,
    annotationId,
    taxonName,
    colors: { node: randomNodeColor(), edge: DEFAULT_EDGE_COLOR },
    onBack: () => {
      destroy();
      onClose();
    },
  });
  scope.append(view.el);

  function destroy() {
    if (destroyed) return;
    destroyed = true;
    view.destroy();
    scope.remove();
  }
  return { destroy };
}
