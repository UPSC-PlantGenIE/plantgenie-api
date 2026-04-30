import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const baseUrl =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/";

export interface Taxon {
  id: number;
  scientificName: string;
  abbreviation: string;
  alias: string | null;
  commonName: string | null;
}

export interface Assembly {
  id: string;
  version: string;
  versionName: string | null;
  published: boolean;
  publicationDate: string | null;
  doi: string | null;
  taxonAbbreviation: string;
}

export interface Annotation {
  id: string;
  version: string;
  geneCount: number;
  isDefault: boolean;
  assemblyId: string;
}

export interface GeneList {
  listId: string;
  name: string;
  annotationId: string;
}

export interface CreateListResponse {
  accountId: string;
  listId: string;
}

export interface CreateListRequest {
  accountId?: string;
  name: string;
  description?: string;
  annotationId: string;
}

export const plantgenieApi = createApi({
  reducerPath: "plantgenieApi",
  baseQuery: fetchBaseQuery({ baseUrl }),
  endpoints: (build) => ({
    getTaxa: build.query<Taxon[], void>({
      query: () => "v2/taxa",
      transformResponse: (r: { taxa: Taxon[] }) => r.taxa,
    }),
    getAssemblies: build.query<Assembly[], { taxon?: string }>({
      query: ({ taxon }) => ({
        url: "v2/assemblies",
        params: { taxon },
      }),
      transformResponse: (r: { assemblies: Assembly[] }) => r.assemblies,
    }),
    getAnnotations: build.query<
      Annotation[],
      { taxon?: string; assembly?: string }
    >({
      query: (params) => ({ url: "v2/annotations", params }),
      transformResponse: (r: { annotations: Annotation[] }) => r.annotations,
    }),
    createList: build.mutation<CreateListResponse, CreateListRequest>({
      query: (body) => ({ url: "v2/lists", method: "POST", body }),
    }),
    getList: build.query<GeneList, string>({
      query: (listId) => `v2/lists/${listId}`,
    }),
    getMyLists: build.query<GeneList[], void>({
      query: () => "v2/lists",
      transformResponse: (r: { lists: GeneList[] }) => r.lists,
    }),
  }),
});

export const {
  useGetTaxaQuery,
  useGetAssembliesQuery,
  useGetAnnotationsQuery,
  useCreateListMutation,
  useGetListQuery,
  useGetMyListsQuery,
} = plantgenieApi;
