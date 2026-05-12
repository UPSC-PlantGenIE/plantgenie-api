import { http, HttpResponse } from "msw";

const taxa = [
  {
    id: 1,
    scientificName: "Pinus sylvestris",
    abbreviation: "pinsy",
    alias: "pinus-sylvestris",
    commonName: "Scots pine",
  },
  {
    id: 2,
    scientificName: "Picea abies",
    abbreviation: "picab",
    alias: "picea-abies",
    commonName: "Norway spruce",
  },
];

const assemblies = [
  {
    id: "pinsy-v2.0",
    version: "v2.0",
    versionName: null,
    published: true,
    publicationDate: "2023-06-15",
    doi: "10.1234/pinsy.v2",
    taxonAbbreviation: "pinsy",
  },
  {
    id: "picab-v1",
    version: "v1",
    versionName: null,
    published: true,
    publicationDate: "2022-03-01",
    doi: "10.1234/picab.v1",
    taxonAbbreviation: "picab",
  },
];

const annotations = [
  {
    id: "pinsy-Araport11",
    version: "Araport11",
    geneCount: 27655,
    isDefault: true,
    assemblyId: "pinsy-v2.0",
  },
  {
    id: "pinsy-TAIR10",
    version: "TAIR10",
    geneCount: 28775,
    isDefault: false,
    assemblyId: "pinsy-v2.0",
  },
  {
    id: "picab-v1-default",
    version: "v1",
    geneCount: 42100,
    isDefault: true,
    assemblyId: "picab-v1",
  },
];

export const handlers = [
  http.post("http://localhost:8000/api/v2/lists", async ({ request }) => {
    const body = (await request.json()) as { accountId?: string };
    return HttpResponse.json({
      accountId: body.accountId ?? "fake-account",
      listId: "fake-list-123",
    });
  }),
  http.get("http://localhost:8000/api/v2/lists", () =>
    HttpResponse.json({
      lists: [
        {
          listId: "abc-123",
          name: "Test list",
          description: "Example list for development",
          annotationId: "arath-Araport11",
          taxonName: "Arabidopsis thaliana",
          createdAt: "2026-04-14T12:00:00",
          geneCount: 12,
        },
      ],
    })
  ),

  http.get(
    "http://localhost:8000/api/v2/lists/:listId",
    ({ params }) => {
      return HttpResponse.json({
        listId: params.listId,
        name: "My fetched list",
        description: null,
        annotationId: "arath-Araport11",
        taxonName: "Arabidopsis thaliana",
        createdAt: "2026-04-14 12:00:00",
        geneCount: 0,
        memberGeneIds: [],
      });
    }
  ),

  http.post(
    "http://localhost:8000/api/v2/genes/lookup",
    async ({ request }) => {
      const body = (await request.json()) as { geneIds: string[] };
      const fixtures: Record<
        string,
        { name: string; description: string }
      > = {
        AT1G01010: { name: "GENE1", description: "First gene" },
        AT1G01020: { name: "GENE2", description: "Second gene" },
      };
      const found = body.geneIds.flatMap((id) =>
        fixtures[id] ? [{ geneId: id, ...fixtures[id] }] : []
      );
      const notFound = body.geneIds.filter((id) => !fixtures[id]);
      return HttpResponse.json({ found, notFound });
    }
  ),

  http.get("http://localhost:8000/api/v2/taxa", ({ request }) => {
    const abbreviation = new URL(request.url).searchParams.get("abbreviation");
    const filtered = abbreviation
      ? taxa.filter((t) => t.abbreviation === abbreviation)
      : taxa;
    return HttpResponse.json({ taxa: filtered });
  }),

  http.get("http://localhost:8000/api/v2/assemblies", ({ request }) => {
    const taxon = new URL(request.url).searchParams.get("taxon");
    const filtered = taxon
      ? assemblies.filter((a) => a.taxonAbbreviation === taxon)
      : assemblies;
    return HttpResponse.json({ assemblies: filtered });
  }),

  http.get("http://localhost:8000/api/v2/annotations", ({ request }) => {
    const url = new URL(request.url);
    const taxon = url.searchParams.get("taxon");
    const assembly = url.searchParams.get("assembly");
    if (taxon && assembly) {
      return HttpResponse.json(
        { detail: "Specify either 'assembly' or 'taxon', not both" },
        { status: 400 }
      );
    }
    let filtered = annotations;
    if (assembly) {
      filtered = filtered.filter((n) => n.assemblyId === assembly);
    } else if (taxon) {
      const assemblyIds = assemblies
        .filter((a) => a.taxonAbbreviation === taxon)
        .map((a) => a.id);
      filtered = filtered.filter((n) => assemblyIds.includes(n.assemblyId));
    }
    return HttpResponse.json({ annotations: filtered });
  }),
];
