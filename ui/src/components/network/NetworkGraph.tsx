import { useEffect, useRef, useState } from "react";
import { baseUrl } from "../../api/plantgenieApi";
import { openNetworkGraph } from "../../networkGraph/feature";
import { useAppSelector } from "../../store/hooks";

interface Props {
  listId: string;
  listName: string;
  annotationId: string;
  taxonName: string;
  onClose: () => void;
}

/**
 * Hosts the network graph feature (plain JS + d3, see src/networkGraph).
 * It renders into the div below: the graph page of the list, which takes over
 * the viewport until it is closed.
 */
export default function NetworkGraph({
  listId,
  listName,
  annotationId,
  taxonName,
  onClose,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const accountId = useAppSelector((state) => state.account.accountId);

  // The feature is built once per open; the latest values are read from
  // refs so a parent re-render does not rebuild (and so reset) the graph.
  const latest = useRef({ accountId, onClose });
  useEffect(() => {
    latest.current = { accountId, onClose };
  });
  const [initial] = useState({ listId, listName, annotationId, taxonName });

  useEffect(() => {
    if (!host.current) return;
    const feature = openNetworkGraph({
      host: host.current,
      apiRoot: `${baseUrl}v2`,
      getHeaders: () => {
        const headers: Record<string, string> = {};
        if (latest.current.accountId)
          headers.Authorization = `Bearer ${latest.current.accountId}`;
        return headers;
      },
      listId: initial.listId,
      listName: initial.listName,
      annotationId: initial.annotationId,
      taxonName: initial.taxonName,
      onClose: () => latest.current.onClose(),
    });
    return () => feature.destroy();
  }, [initial]);

  return <div ref={host} />;
}
