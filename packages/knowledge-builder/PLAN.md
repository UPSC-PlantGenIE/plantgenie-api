# knowledge-builder

A graph-driven build system for the PlantGenie Neo4j knowledge graph. A
single `kb` command runs end-to-end: connects to Neo4j, reads
`knowledge.yaml`, MERGEs the catalog into the graph, runs DuckDB to produce
derived CSVs into `/opt/neo4j/import`, then runs Cypher LOAD CSV to populate
the application graph.

`DATA_MODEL.md` and `knowledge.yaml` are the two source-of-truth files.
Everything else is implementation.

## Current state (2026-06-11)

### Pipeline shape

`kb` is a `typer` app with two subcommands:

**`uv run kb build`** runs the full graph build, top to bottom:

1. Load `.env.shared` then `.env`, verify `NEO4J_URI` / `NEO4J_USER` /
   `NEO4J_PASSWORD`, connect, `verify_connectivity()`.
2. Read `knowledge.yaml`.
3. Run `cypher/merge_domain.cypher` — MERGE `Taxon` / `Assembly` /
   `Annotation` nodes and `OF` edges. The yaml→params loop in
   `main.py` materialises the extra `Assembly --OF--> taxon` row for
   each entry in a taxon's `uses:` block (currently just `pinco`).
4. Run `cypher/merge_build.cypher` — MERGE source + derived `Asset`,
   `BuildStep`, `LoadStep` nodes, and `FROM` / `READ_BY` / `WRITES` /
   `REQUIRES` edges.
5. Download `go-basic.json` via `httpx` (logged start/finish),
   `json.load` it, write `/tmp/knowledge-builder/go-basic-nodes.ndjson`
   and `go-basic-edges.ndjson`. Done in Python because DuckDB's
   `read_json` on the monolithic 70 MB nested object is its slow path;
   NDJSON is its fast path.
6. Run `sql/build.sql` — one DuckDB connection, multi-statement
   `con.execute()`. Produces all derived CSVs into `/opt/neo4j/import/`.
7. Run `cypher/load.cypher` — `session.run()` per statement. LOAD CSV
   every derived CSV into Neo4j and create the application-graph nodes
   (`Gene`, `GoTerm`) and their edges (`OF`, `HAS_GO`, `IS_A`,
   `PART_OF`).
8. Print a graph report: per-label node counts (Taxon, Assembly,
   Annotation, Asset, BuildStep, LoadStep, Gene, GoTerm) and a
   per-annotation table of Gene + HAS_GO counts.

**`uv run kb sync`** walks every yaml asset with `object:` set,
cross-checks against the bucket listing, prints present/missing, and
uploads each missing source asset via a bespoke
`fetch_<species>_genome` function (FTP via `ftplib` for potra; HTTPS
via `httpx` for arath/pruav with `verify=False` for broken cert chains,
betpe with no `verify=False` needed). Uses `SwiftClient` from
`packages/shared` (auth via OpenStack application credential from
`.env.shared`).

Total `kb build` run time on the dev box is on the order of a few
minutes.

### What's in the graph

Seven annotations across six taxa loaded end-to-end (`pinco` shares
pinsy's assembly + annotation via the `uses:` cross-link, so it gets
the same Gene + HAS_GO via the chain — not a separate row):

| taxon | annotation | Gene | HAS_GO |
|---|---|---|---|
| arath | `arath/tair10/araport11` | 27,655 | 0 |
| arath | `arath/tair10/tair10` | 28,775 | 0 |
| betpe | `betpe/v1/v1.2` | 27,356 | ~699K |
| picab | `picab/v2/v2.0` | 43,382 | ~990K |
| pinsy | `pinsy/v1/v1.0` | 49,387 | ~1.00M |
| potra | `potra/v2/v2.2` | 37,184 | ~966K |
| pruav | `pruav/v2/v2.0` | 39,984 | ~802K |

Distinct Gene nodes after MERGE-by-id: 226,805 (less than the
per-annotation sum because tair10 and araport11 share AT-prefix gene
ids). Distinct HAS_GO: ~4.46M.

Plus 51,967 `GoTerm`, 57,803 `IS_A`, 6,272 `PART_OF` from the GO
ontology (loaded once via `shared/build-go-terms` →
`shared/load-go-terms`).

arath has no eggnog and no GO source, so neither annotation has a
`build-gene-go` / `load-gene-go` step — modelled by simply omitting
those steps in `knowledge.yaml`, exactly as the user wants ("an
annotation can simply have no GO terms"). araport11 has a derived
`functional-descriptions` asset (extracted from the gff attributes by
a `BuildStep` whose output is consumed by another `BuildStep` — first
build-feeds-build chain in the graph). tair10 reads the source
`TAIR10_functional_descriptions` file inline.

Build half: ~31 `Asset`, ~14 `BuildStep`, ~13 `LoadStep`.

### Bucket state

All seven genomes are now in the `plantgenie-knowledge` bucket:

| taxon | object | how it got there |
|---|---|---|
| arath | `Arabidopsis_thaliana.TAIR10.dna.toplevel.fa.gz` | `kb sync` → `fetch_arath_genome` |
| betpe | `Bepen_v1p2_genome.fa` | `kb sync` → `fetch_betpe_genome` |
| picab | `Picab02_chromosomes_and_unplaced.fa.gz` | manual `client.stream_upload` (no `source_url`) |
| pinsy | `Pinsy01_chromosomes_and_unplaced.fa.gz` | manual `client.stream_upload` (no `source_url`) |
| potra | `Potra02_genome.fasta.gz` | manual `client.upload` from local copy (FTP source flaky) |
| pruav | `Tieton02_genome.fasta.gz` | `kb sync` → `fetch_pruav_genome` |

picab and pinsy don't have `source_url` in yaml (uploaded from local
copies) — `kb sync` still sees them as present because `object:` is
declared.

Non-genome source assets (gffs, eggnog, functional-descriptions) were
uploaded out of band before this work started (some are pre-sorted /
renamed versions of upstream files); `kb sync` doesn't try to
reproduce them — that would require a separate normalize step.

### File layout

```
packages/knowledge-builder/
├── DATA_MODEL.md
├── knowledge.yaml
├── PLAN.md                                  # this file
├── pyproject.toml                           # deps: neo4j, duckdb, httpx, pyyaml,
│                                            #       typer, python-dotenv, structlog,
│                                            #       jinja2 (unused now)
└── src/knowledge_builder/
    ├── __init__.py                          # re-exports main.app as main
    ├── main.py                              # the whole kb build flow (~180 lines)
    ├── cypher/
    │   ├── merge_domain.cypher              # 3 statements
    │   ├── merge_build.cypher               # 9 statements
    │   └── load.cypher                      # CREATE INDEX + awaitIndexes +
    │                                        # LOAD CSV per derived CSV
    └── sql/
        └── build.sql                        # every DuckDB COPY block, one file
```

`domain.py`, `steps/`, and the old `cli.py` are leftovers from earlier
experiments and are orphaned — nothing imports them. Safe to delete.

### Design decisions worth carrying forward

- **The graph is the build plan.** `BuildStep` / `LoadStep` are nodes; the
  yaml is a declarative description; the Python script is just an executor
  that runs MERGE → DuckDB → LOAD CSV in order. No per-step Python
  functions, no CLI subcommand per step.
- **DuckDB reads bucket source assets straight from URLs.** No pre-fetch
  step for the gff / eggnog files — they're streamed by `read_csv` over
  HTTPS each run. Pre-fetch with `httpx` is reserved for things DuckDB's
  reads can't handle well (GO JSON), or sources that don't speak HTTPS
  (FTP, when we get there).
- **SQL/Cypher live in files, not in code.** `cypher/*.cypher` and
  `sql/build.sql` are the operational source of truth; main.py reads them
  verbatim. New taxa = a yaml block + a SQL `COPY` block + a Cypher
  LOAD CSV block. No splitters, no templating engine, no `sqlfluff` parse —
  splitting on `;` works for Cypher because our Cypher has no semicolons
  inside literals; SQL is passed whole to DuckDB.

## Next steps

### Derived genome assets (next chunk — design agreed, not started)

Now that all seven genomes are in the bucket, the next work is the
derived assets the API runtime needs (not Neo4j — these are not LOAD
CSV inputs). They cluster into two layers:

**Per-assembly (genome → ...):**
- bgzipped + faidx-indexed FASTA (random access via samtools / htslib)
- BLAST nucleotide DB (`makeblastdb -dbtype nucl`)

**Per-annotation (gff + genome → ... via `gffread`):**
- CDS FASTA
- mRNA / transcript FASTA
- protein FASTA
- BLAST protein DB (`makeblastdb -dbtype prot`)
- DIAMOND DB (`diamond makedb`)

Each is its own `Asset` node, written by its own bespoke `BuildStep`
function in `main.py` — one Python function per asset, single
`subprocess.run` per tool. Flat list, no shared helpers, ~50 step
entries in `knowledge.yaml` across 7 taxa. The user has been explicit
about this: don't extract anything; errors will come from sources, not
from code organisation, and a flat ugly file is the correct shape.

#### Design decisions

**(1) Where do derived assets live?** All synced to the bucket. The
bucket is the source of truth for "is this built." A future build
manifest will compute a hash of the locally-built asset and compare
against the bucket etag to decide whether to rerun the upstream
`BuildStep`; downstream `LoadStep`s rerun automatically when an asset
they `READ_BY` changes. (User's explicit answer.)

**(2) What runtime runs the build?** Create
`packages/knowledge-builder/Dockerfile` that uses the top-level
`Dockerfile.tools` as its base image (which ships `bgzip`, `samtools`,
`gffread`, `makeblastdb`, `diamond`), then layers Python + uv +
`knowledge-builder` source on top — same shape as
`packages/task-queue/Dockerfile`. `kb` then runs in that container and
each derived-asset `BuildStep` just calls `subprocess.run(...)` against
the tools on PATH. (User's explicit answer.)

**(3) Bucket caching.** Implicit from (1) — always cached.

**(4) Build graph edges.** Same `READ_BY` / `WRITES` model as today.
Derived `Asset` entries get `object:` set so the upload side of
`kb sync` (still to be added — currently sync only fetches from
external sources) can push them back to the bucket. Hash/etag
staleness comparison is the build manifest work below — deferred.

#### Handoff plan (smallest next chunk for a fresh session)

1. **Create `packages/knowledge-builder/Dockerfile`** modeled on
   `packages/task-queue/Dockerfile`. `FROM` the top-level
   `Dockerfile.tools` for the binaries, then layer
   `python:3.13-slim-bookworm` + `uv` + the `knowledge-builder`
   package on top. Result: a `kb` container with all the
   bioinformatics tools available on PATH and the Python entrypoint
   working.

2. **Pick one assembly and build the bgzip + faidx pair end-to-end.**
   Suggest picab (smallest big-genome upload; we have it locally and
   in the bucket). Concretely:
   - In `knowledge.yaml`, under the picab assembly's `assets:` block,
     add two new derived `Asset` entries: `genome-bgz` and
     `genome-fai`. Both get `object:` set (e.g.
     `Picab02_chromosomes_and_unplaced.fa.gz` is already the bgzipped
     name — clarify naming with the user; faidx output ends `.fai`).
   - Add a `BuildStep` to `steps:` that reads
     `picab/v2/genome` and writes both derived assets.
   - Add a `build_picab_genome_bgz_fai` function in `main.py` that:
     downloads the source genome from the bucket to a temp dir
     (`client.download_object` already exists in `SwiftClient`), runs
     `bgzip` if not already bgzipped, runs `samtools faidx`, then
     uploads both outputs back to the bucket via `client.upload`.
   - Run it in the container, confirm the outputs land in the bucket.

3. **Then write the same function shape per-assembly** for the
   remaining 6. Flat list, one function each, no extraction even at
   7 of them.

4. **Build manifest / staleness — DEFER.** Don't design or wire it
   yet. Every `kb build` rebuilds everything for now. The hash/etag
   comparison comes after we have a working set of derived assets.

5. **`kb sync` upload side for derived assets — DEFER.** The current
   `kb sync` walks yaml and uploads missing *source* assets; the
   derived-asset functions above upload directly. A unified upload
   pass via `kb sync` for derived assets comes later, when staleness
   tracking arrives.

#### Open questions for the new session

- Naming for the bgzipped/faidx outputs. picab is already named
  `Picab02_chromosomes_and_unplaced.fa.gz` — is that already a
  bgzipped gzip, or just a plain gzip? `bgzip` and `gzip` produce
  files that both decode as gzip but only bgzip is faidx-indexable.
  Check before deciding whether the existing `.gz` is the bgz or
  whether we need to upload a separate `*.bgz` / `*.fa.gz` pair.
- arath and betpe genomes are NOT bgzipped at source (`.fa.gz` from
  Ensembl is gzip; `Bepen_v1p2_genome.fa` is uncompressed). The
  bgzip step has to handle both gzip-decompress-then-bgzip and
  plain-bgzip cases.
- Does the API runtime read directly from the bucket (DuckDB-style
  URL reads — fine for samtools when files are HTTPS-accessible
  via htslib) or does it expect a local mount? Determines whether
  `kb sync` needs to populate a local cache dir on hosts that run
  the API.

### Build manifest / staleness

Currently every `kb` run does everything. The old
`/opt/plantgenie/.knowledge-pipeline-state.json` tracked per-`<file>:<consumer>`
ETag + `last_loaded`. The clean mapping into the graph:

- `etag` + `last_fetched_at` on source `Asset` nodes (HEAD request against
  `bucketUri`; cheap).
- `last_etag` + `last_read_at` on `READ_BY` edges (per-consumer cursor).
- A step is stale iff any incoming `READ_BY` edge has `last_etag <>
  Asset.etag` or is null.

Defer until parity is reached across all taxa.

### Known data-quality issues

- **3 orphan `Gene` nodes** (`HAS_GO` but no `OF`), accounting for ~67
  HAS_GO edges. The betpe `chromosome Contig0` orphan is almost certainly
  an eggnog tsv parse artifact and worth investigating.
- **Gene `id` collisions across taxa are possible.** Load Cypher MERGEs
  Gene by `id` only, no taxon scoping. Distinct prefixes per species
  ([Bpev*], `Picab02_*`, `Pinsy01_*`, etc.) make collision very unlikely
  in practice, but Gene id should probably be qualified by annotation
  long-term.
- **`geneCount` mismatch in yaml** for picab/pinsy (the `*_longest_no_TE`
  files are pre-filtered). The user has indicated this will be reconciled
  separately — do not edit `geneCount` here.
- **GO term aliases** (alt_id → canonical) are skipped; the old SQL
  produced `go-aliases.csv`. Add if a consumer needs them.

### DATA_MODEL.md open questions still open

1. `BuildStep` cardinality invariant (≥1 READ_BY / ≥1 WRITES — hard
   constraint or just convention?).
2. Asset / step properties beyond what's settled (`bucket_uri`, `format`).
3. Domain-free source assets — the `shared:` block now exists in
   `knowledge.yaml` for GO; formal spec for other ontologies / DBs not yet
   written.
4. Cross-taxon derived assets (DIAMOND hits, ortholog groups) — id form
   not decided.

### Operational notes

- `cypher/load.cypher` must keep `CALL db.awaitIndexes()` between the two
  `CREATE INDEX` statements and the first `LOAD CSV`. Without it the LOAD
  CSV runs before the index is online and re-runs the ~50-minute
  label-scan path.
- `/opt/neo4j/import/` is shared across worktrees per the docker-compose
  mount. Concurrent multi-worktree builds writing the same filenames would
  race. Not a today-blocker but worth knowing.
- DuckDB's progress bar (`PRAGMA enable_progress_bar`) renders for table
  scans but **not** for `read_json` over HTTP — that's why the GO download
  is in Python: explicit visible progress, faster path overall.
