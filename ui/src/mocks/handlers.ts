import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('http://localhost:8000/api/v1/available-species', () =>
    HttpResponse.json({
      species: [
        {
          id: 1,
          speciesName: 'Pinus sylvestris',
          speciesAbbreviation: 'pinus-sylvestris',
          avatarPath: 'pinsy',
        },
        {
          id: 2,
          speciesName: 'Picea abies',
          speciesAbbreviation: 'picea-abies',
          avatarPath: 'picab',
        },
      ],
    }),
  ),
]
