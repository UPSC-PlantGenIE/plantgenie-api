import { plantgenieApi } from "./plantgenieApi";

export const MAX_RANDOM_GENES = 100;

export const randomGenesApi = plantgenieApi.injectEndpoints({
  endpoints: (build) => ({
    addRandomGenes: build.mutation<
      { added: number },
      { listId: string; count: number }
    >({
      query: ({ listId, count }) => ({
        url: `v2/lists/${listId}/random-genes`,
        method: "POST",
        body: { count },
      }),
      invalidatesTags: ["List"],
    }),
  }),
});

export const { useAddRandomGenesMutation } = randomGenesApi;
