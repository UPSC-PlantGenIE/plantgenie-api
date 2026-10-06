import { plantgenieApi } from "./plantgenieApi";

export const DEFAULT_NUMBER_OF_RESULTS = 10;

export interface SemanticSpecies {
  abbreviation: string;
  scientificName: string;
}

export interface SemanticSearchHit {
  geneId: string;
  description: string;
  similarity: number;
}

export interface SemanticSearchArgs {
  species: string;
  query: string;
  numberOfResults?: number;
}

export const semanticSearchApi = plantgenieApi.injectEndpoints({
  endpoints: (build) => ({
    getSemanticSpecies: build.query<SemanticSpecies[], void>({
      query: () => "v2/semantic-search/species",
    }),
    semanticSearch: build.query<SemanticSearchHit[], SemanticSearchArgs>({
      query: ({ species, query, numberOfResults = DEFAULT_NUMBER_OF_RESULTS }) => ({
        url: "v2/semantic-search",
        params: { species, query, number_of_results: numberOfResults },
      }),
    }),
  }),
});

export const { useGetSemanticSpeciesQuery, useSemanticSearchQuery } =
  semanticSearchApi;

/** Finds the semantic-search species matching a list's taxon name. */
export const findSemanticSpecies = (
  species: SemanticSpecies[] | undefined,
  taxonName: string | undefined
): SemanticSpecies | undefined => {
  if (!species || !taxonName) return undefined;
  const wanted = taxonName.trim().toLowerCase();
  return species.find((s) => s.scientificName.toLowerCase() === wanted);
};
