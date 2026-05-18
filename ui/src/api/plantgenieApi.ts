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

export interface AnnotationDetail extends Annotation {
  taxonAbbreviation: string;
  taxonScientificName: string;
}

export interface GeneList {
  listId: string;
  name: string;
  description: string | null;
  annotationId: string;
  taxonName: string;
  createdAt: string;
  geneCount: number;
}

export interface GeneListWithMembers extends GeneList {
  memberGeneIds: string[];
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
  taxonName: string;
}

export interface LookupGene {
  geneId: string;
  name: string | null;
  description: string | null;
}

export interface LookupGenesResponse {
  found: LookupGene[];
  notFound: string[];
}

export const plantgenieApi = createApi({
  reducerPath: "plantgenieApi",
  baseQuery: fetchBaseQuery({ baseUrl }),
  tagTypes: ["List"],
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
    getAnnotation: build.query<AnnotationDetail, string>({
      query: (annotationId) => `v2/annotations/${annotationId}`,
    }),
    createList: build.mutation<CreateListResponse, CreateListRequest>({
      query: (body) => ({ url: "v2/lists", method: "POST", body }),
      invalidatesTags: ["List"],
    }),
    getList: build.query<GeneListWithMembers, string>({
      query: (listId) => `v2/lists/${listId}`,
      providesTags: ["List"],
    }),
    getMyLists: build.query<GeneList[], void>({
      query: () => "v2/lists",
      transformResponse: (r: { lists: GeneList[] }) => r.lists,
      providesTags: ["List"],
    }),
    lookupGenes: build.query<
      LookupGenesResponse,
      { annotationId: string; geneIds: string[] }
    >({
      query: (body) => ({
        url: "v2/genes/lookup",
        method: "POST",
        body,
      }),
    }),
    patchList: build.mutation<
      { listId: string },
      {
        listId: string;
        addGeneIds?: string[];
        removeGeneIds?: string[];
      }
    >({
      query: ({ listId, ...body }) => ({
        url: `v2/lists/${listId}`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["List"],
    }),
    deleteList: build.mutation<void, string>({
      query: (listId) => ({
        url: `v2/lists/${listId}`,
        method: "DELETE",
      }),
      invalidatesTags: ["List"],
    }),
  }),
});

export const {
  useGetTaxaQuery,
  useGetAssembliesQuery,
  useGetAnnotationsQuery,
  useGetAnnotationQuery,
  useCreateListMutation,
  useGetListQuery,
  useGetMyListsQuery,
  useLookupGenesQuery,
  useLazyLookupGenesQuery,
  usePatchListMutation,
  useDeleteListMutation,
} = plantgenieApi;
