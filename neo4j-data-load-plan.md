# Neo4j data load plan

Populating the dev neo4j store so the new UI (which calls only `/v2/*`) has
real content. Source material is in `~/Projects/upsc-plantgenie`, left over
from the arcadedb experiment.

## What already exists

| Piece | Location | State |
|---|---|---|
| CSV generation | `upsc-plantgenie/generate-neo4j-records.sql` | Neo4j-targeted already. DuckDB reads GFF3 + eggnog straight from Swift URLs and writes tab-delimited CSVs to `/opt/neo4j/import/`. |
| Generated CSVs | `upsc-plantgenie/database-imports/` | Already produced. No need to re-run DuckDB. |
| GO graph + gene loads | `upsc-plantgenie/neo4j-queries.cypher` | Real Neo4j 5 syntax (`CALL (row) { … } IN TRANSACTIONS`). Terms, IS_A/PART_OF, alt-id aliases, per-annotation genes, gene→GO with alias resolution. |
| Domain seed | `upsc-plantgenie/arcadedb/{taxon,assembly,annotation}-load.cypher` | ArcadeDB dialect and paths. **Needs porting.** |

`neo4j-queries.cypher` only ever `MATCH`es `Annotation` nodes, never creates
them, so the domain seed is the missing link between the two.

## Gaps

### 1. ID scheme conflict

Two incompatible schemes are in play:

- Slash paths (`betpe/v1/v1.2`, `arath/tair10/araport11`) in the arcadedb loads
  and in `database-imports/*.csv`
- Hyphens (`betpe-v1.2`, `arath-Araport11`, `pinsy-v1.0`) in
  `neo4j-queries.cypher` and throughout the v2 API and its tests

Hyphens win, and not by preference: `/v2/annotations/{annotation_id}` is a
single path segment, so a slash-containing ID would never route.

### 2. Required model properties missing from the CSVs

`PlantGenieModel` sets `extra="forbid"`, and these fields have no defaults:

| Field | Model | Present in CSV? |
|---|---|---|
| `published: bool` | `Assembly` | No. `assemblies.csv` has only `id,taxon,version`. |
| `gene_count: int` | `Annotation` | No. `annotations.csv` has only `id,assembly,version`. |
| `is_default: bool` | `Annotation` | No. |

`/v2/assemblies` and `/v2/annotations` will return 500 on response validation
after an otherwise clean load. `versionName`, `publicationDate` and `doi` are
`Optional`, so their absence is fine.

`geneCount` is computable after the gene load; the summary query at the end of
`neo4j-queries.cypher` already produces exactly that number.

### 3. Missing arath data

`taxa.csv` lists 7 taxa and `annotations.csv` 7 annotations, but
`database-imports/` has gene CSVs for only 5: betpe, picab, pinsy, potra,
pruav.

- `generate-neo4j-records.sql` has `COPY … TO 'arath-araport11-gene-records.csv'`
  and `arath-tair10-gene-records.csv`, but neither file was ever produced
- There is no `arath-*-gene-go` COPY target at all
- `neo4j-queries.cypher` loads both arath files regardless
- `pinco` (taxon 7) has no assembly

The v2 unit tests use `arath-Araport11`, so this will be noticed.

### 4. Delimiters

Reference CSVs (`taxa`, `assemblies`, `annotations`, `experiments`) are
comma-delimited; generated data CSVs are tab-delimited. Both existing cypher
sets already handle this with `FIELDTERMINATOR '\t'`.

## Out of scope

The coexpression and expression CSVs (~500MB) and `experiments.csv`. No v2
endpoint reads them and the new UI calls none. In-scope files total ~150MB.

## Decisions needed

- [x] IDs: nodes carry both a URL-safe `id` (`betpe-v1`, `betpe-v1.2`) and a
      `path` holding the disk layout (`betpe/v1`). Annotation IDs match those
      the gene loads in `neo4j-queries.cypher` already expect.
- [x] `published` is `false` for all six assemblies for now.
- [ ] Which annotation is `isDefault` for arath, araport11 or tair10? Moot
      until the arath gene CSVs exist.
- [ ] Produce the arath gene CSVs. Both arath rows are currently dropped from
      `annotations.csv`, so Arabidopsis shows "No genomes available" in the
      wizard. Two lines to add back once the CSVs exist.
- [ ] Where do the load scripts live long-term? The api repo has the neo4j
      deployment (`infra/neo4j.tf`, `infra/neo4j-cloud-init.yaml`), but
      knowledge-builder was the intended home.

## Load order

Each step depends on the one above it.

1. ~~**Taxon** — from `taxa.csv`. No gaps, no ID conflict.~~ Done 2026-09-02
   via `scripts/neo4j/taxon-load.cypher`. All 7 taxa serve correctly from
   `/v2/taxa`, and the new UI picks them up in the create-list flow.
2. ~~**Assembly** — needs hyphenated IDs and a `published` column.~~ Done
   2026-09-02 via `scripts/neo4j/assembly-load.cypher`. Six assemblies,
   serving from `/v2/assemblies`. Required adding `path` to the `Assembly`
   model, since that query returns the whole node and `extra="forbid"` would
   otherwise reject it.
3. ~~**Annotation** — needs hyphenated IDs and an `isDefault` column.~~ Done
   2026-09-02 via `scripts/neo4j/annotation-load.cypher`. Five annotations,
   arath excluded. No model change needed: that query already projects
   `n {.id, .version, .geneCount, .isDefault}`, so `path` never reaches
   pydantic. The wizard's genome selector now populates.
4. ~~**GO graph** — terms, edges, aliases.~~ Done 2026-09-02 via
   `scripts/neo4j/go-load.cypher`. The two separate IS_A and PART_OF passes
   from `neo4j-queries.cypher` are combined into one using a dynamic
   relationship type, `CREATE (from)-[:$(row.type)]->(to)`.
5. ~~**Genes** — per annotation.~~ Done 2026-09-02 via
   `scripts/neo4j/gene-load.cypher`. Five annotations, arath omitted.
6. ~~**Gene→GO**.~~ Done 2026-09-02 via `scripts/neo4j/gene-go-load.cypher`.
7. **`geneCount`** — likely unnecessary. The values already on the Annotation
   nodes came from the gene-records row counts, so this only matters if the
   gene load's verification returned different numbers.

## Remaining

The graph is loaded for the five taxa that have data. What is left:

- Arabidopsis: generate the gene CSVs, add the two rows back to
  `annotations.csv`, decide `isDefault`
- Real `published`, `versionName`, `publicationDate` and `doi` values for the
  assemblies, all currently absent or `false`
- Repeat the load on the dev VM, which is the original TODO item

## Local test setup

`docker-compose.yaml` scopes the neo4j store per worktree:

```yaml
- /opt/neo4j/${WORKTREE:?WORKTREE must be set in .env}/logs:/logs
- /opt/neo4j/${WORKTREE:?WORKTREE must be set in .env}/data:/data
- /opt/neo4j/import:/import:ro
```

`WORKTREE` must come from `.env`, not `.env.shared` — compose only reads the
shell environment or `.env` for `${...}` interpolation, and `.env.shared`
values are quoted, so `--env-file` would embed the quotes in the path.
Currently `WORKTREE=main`, giving `/opt/neo4j/main/`.

Run a load script against the local stack by piping it in, which avoids
writing to the read-only shared import directory:

```
docker compose exec -T neo4j cypher-shell -u neo4j -p guest123 < scripts/neo4j/taxon-load.cypher
```
