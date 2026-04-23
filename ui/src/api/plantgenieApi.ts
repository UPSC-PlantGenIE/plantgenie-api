import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

const baseUrl =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1/'

export interface Species {
  id: number
  speciesName: string
  speciesAbbreviation: string
  avatarPath: string
}

interface AvailableSpeciesResponse {
  species: Species[]
}

export const plantgenieApi = createApi({
  reducerPath: 'plantgenieApi',
  baseQuery: fetchBaseQuery({ baseUrl }),
  endpoints: (build) => ({
    getSpecies: build.query<Species[], void>({
      query: () => 'available-species',
      transformResponse: (r: AvailableSpeciesResponse) => r.species,
    }),
  }),
})

export const { useGetSpeciesQuery } = plantgenieApi
