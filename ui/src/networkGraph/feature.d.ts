export interface NetworkGraphOptions {
  host: HTMLElement;
  /** URL of the v2 API, e.g. http://host/api/v2 */
  apiRoot: string;
  getHeaders?: () => Record<string, string>;
  listId: string;
  listName?: string;
  annotationId?: string;
  taxonName?: string;
  onClose?: () => void;
}

export function openNetworkGraph(options: NetworkGraphOptions): {
  destroy: () => void;
};
