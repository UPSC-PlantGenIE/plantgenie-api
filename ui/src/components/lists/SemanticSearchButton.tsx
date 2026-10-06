import { Link } from "wouter";
import {
  findSemanticSpecies,
  useGetSemanticSpeciesQuery,
} from "../../api/semanticSearchApi";

interface Props {
  listId: string;
  taxonName: string;
  className: string;
}

/**
 * "Search genes" entry point. Active only when the list's species has
 * semantic-search embeddings; otherwise it is dimmed with a tooltip.
 */
export default function SemanticSearchButton({
  listId,
  taxonName,
  className,
}: Props) {
  const { data: species } = useGetSemanticSpeciesQuery();
  const supported = findSemanticSpecies(species, taxonName) !== undefined;

  if (!supported) {
    return (
      <span
        role="link"
        aria-disabled="true"
        title="Not applicable yet"
        className={`${className} cursor-not-allowed opacity-50`}
      >
        🔍 Search genes
      </span>
    );
  }

  return (
    <Link href={`/lists/${listId}/search`} className={className}>
      🔍 Search genes
    </Link>
  );
}
