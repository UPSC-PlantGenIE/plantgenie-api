export class ApiError extends Error {}

/**
 * root        URL of the v2 API, e.g. http://host/api/v2
 * getHeaders  extra headers per request (the account's Authorization)
 */
export function createApi(root = "", getHeaders = () => ({})) {
  async function request(path, { method = "GET", body } = {}) {
    let res;
    try {
      res = await fetch(root + path, {
        method,
        headers: {
          ...getHeaders(),
          ...(body ? { "Content-Type": "application/json" } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new ApiError("Could not reach the server. Please try again.");
    }
    if (!res.ok) {
      let msg = `Request failed (${res.status})`;
      try {
        const { detail } = await res.json();
        if (typeof detail === "string") msg = detail;
        else if (Array.isArray(detail) && detail[0]?.msg)
          msg = `Invalid input: ${detail[0].msg}`;
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(msg);
    }
    return res.json();
  }
  return {
    /** The expression experiments of an annotation (the ones the heatmap offers). */
    experiments: async (annotationId) =>
      (
        await request(
          `/annotations/${encodeURIComponent(annotationId)}/experiments`
        )
      ).experiments,
    /** body = { listId, geneIds?, experimentIds } */
    graph: (body) => request("/network-graph/graph", { method: "POST", body }),
    /** Save genes as a new list (POST /lists, then PATCH to add the genes). */
    async exportList({ name, description, annotationId, taxonName, geneIds }) {
      const { listId } = await request("/lists", {
        method: "POST",
        body: {
          name,
          description: description || null,
          annotationId,
          taxonName,
        },
      });
      await request(`/lists/${encodeURIComponent(listId)}`, {
        method: "PATCH",
        body: { addGeneIds: geneIds },
      });
      return { listId };
    },
  };
}
