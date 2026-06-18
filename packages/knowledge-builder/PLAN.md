# knowledge-builder

A graph-driven build system for the PlantGenie Neo4j knowledge graph. A
single `kb` command runs end-to-end: connects to Neo4j, reads
`knowledge.yaml`, MERGEs the catalog into the graph, runs DuckDB to produce
derived CSVs into `/opt/neo4j/import`, then runs Cypher LOAD CSV to populate
the application graph.

`DATA_MODEL.md` and `knowledge.yaml` are the two source-of-truth files.
Everything else is implementation.

## Current state (2026-06-15)

### Pipeline shape

`kb` is a `typer` app with two subcommands:

`kb` now ships as a Docker image (`packages/knowledge-builder/Dockerfile`)
that bundles `bgzip`, `samtools`, `tabix`, `gffread`, BLAST+, and DIAMOND
on PATH alongside the Python entrypoint. The top-level `Dockerfile.tools`
is orphaned and can be deleted in a follow-up. Typical run shape:

```bash
docker run --rm \
-v $(pwd)/.env.shared:/app/.env.shared:ro \
-v $(pwd)/.env:/app/.env:ro \
-v /opt/neo4j/import:/opt/neo4j/import \
--network api-new-knowledge-builder_plantgenie_network \
plantgenie-kb:dev build
```

**`uv run kb build`** (or `docker run … plantgenie-kb:dev build`) runs the
full graph build, top to bottom:

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
5. Run any registered `BuildStep` whose id appears in `STEP_BUILDERS`
   (a `{step_id: function}` dict in `main.py`). Each registered builder
   gets `(SwiftClient, container)` and does its own
   download → tool invocation → upload. Currently registered:
   `betpe/v1/v1.2/build-gffread`. Steps not in `STEP_BUILDERS` are
   no-ops here (the DuckDB phase below handles gene-records / gene-go).
6. Download `go-basic.json` via `httpx` (logged start/finish),
   `json.load` it, write `/tmp/knowledge-builder/go-basic-nodes.ndjson`
   and `go-basic-edges.ndjson`. Done in Python because DuckDB's
   `read_json` on the monolithic 70 MB nested object is its slow path;
   NDJSON is its fast path.
7. Run `sql/build.sql` — one DuckDB connection, multi-statement
   `con.execute()`. Produces all derived CSVs into `/opt/neo4j/import/`.
8. Run `cypher/load.cypher` — `session.run()` per statement. LOAD CSV
   every derived CSV into Neo4j and create the application-graph nodes
   (`Gene`, `GoTerm`) and their edges (`OF`, `HAS_GO`, `IS_A`,
   `PART_OF`).
9. Print a graph report: per-label node counts (Taxon, Assembly,
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
├── Dockerfile                               # 3 stages: tool-builder, py-builder,
│                                            # final (python+venv+tools+yaml)
├── knowledge.yaml
├── PLAN.md                                  # this file
├── pyproject.toml                           # deps: neo4j, duckdb, httpx, pyyaml,
│                                            #       typer, python-dotenv, structlog,
│                                            #       jinja2 (unused now)
└── src/knowledge_builder/
    ├── __init__.py                          # re-exports main.app as main
    ├── main.py                              # whole kb build flow, fetch_*/build_*
    │                                        # step functions, STEP_BUILDERS dispatch
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

### Derived genome assets — status

Two layers, both per-taxon flat-list (one bespoke Python function each,
no shared helpers — confirmed design):

**Per-assembly (genome → ...):**
- bgzipped + faidx-indexed FASTA (random access via samtools / htslib)
- BLAST nucleotide DB (`makeblastdb -dbtype nucl`)

**Per-annotation (gff + genome → ... via `gffread`):**
- CDS FASTA (bgzipped + faidx)
- mRNA / transcript FASTA (bgzipped + faidx)
- protein FASTA (bgzipped + faidx)
- BLAST protein DB (`makeblastdb -dbtype prot`)
- DIAMOND DB (`diamond makedb`)

#### Done in earlier sessions

- `packages/knowledge-builder/Dockerfile` exists and builds; bundles
  `bgzip` / `samtools` / `tabix` / `gffread` / BLAST+ / DIAMOND. Image
  layout mirrors the dev tree (`/app/packages/knowledge-builder/…`)
  so `main.py`'s `REPO_ROOT` / `PACKAGE_ROOT` arithmetic works inside
  the container. `knowledge.yaml` is baked in; env files mount at
  `/app/.env.shared` and `/app/.env`; `/opt/neo4j/import` mounts
  through so `LOAD CSV` and the DuckDB CSV writes share a directory.
- picab + pinsy `genome-fai` and `genome-gzi` `Asset` entries added to
  yaml; user uploaded the four index files to the bucket from local
  copies (genome was already bgzipped at source for these two — the
  existing `.fa.gz` *is* the bgz).
- `betpe/v1/v1.2/build-gffread` end-to-end: 9 outputs (`cds`, `mrna`,
  `protein` × `.fa.gz` / `.fa.gz.fai` / `.fa.gz.gzi`) uploaded; new
  yaml entry uses `object:` on each `writes:` entry, enabled by a
  one-line tweak to `main.py`'s `writes` loop that lets `object` and
  `bucketUri` flow through.
- `STEP_BUILDERS` registry + dispatch pass inside `kb build` between
  the merge and GO phases. `kb build` now requires the swift env vars
  in addition to the neo4j ones.

#### Done in today's session (2026-06-15)

- Added `betpe/v1/build-genome-bgz-fai` step + yaml entries: renamed
  the existing `betpe/v1/genome` Asset to `genome-source` (raw
  `Bepen_v1p2_genome.fa` with `lcl|` prefix), added derived `genome`
  / `genome-fai` / `genome-gzi` triplet for the bgz outputs. Step
  reads `genome-source`, writes the triplet.
- Added `build_betpe_v1_genome_bgz_fai(client, container)` to
  `main.py` and registered it: downloads `genome-source` from bucket,
  `sed`s out `lcl|`, `bgzip -f`, `samtools faidx`, uploads triplet.
- Rewired `build_betpe_v1_v1_2_gffread` to consume the bgz triplet
  instead of the plain `.fa` and dropped the inline `sed` lcl-strip
  (the bgz is already cleaned). Step's `reads:` already pointed at
  `betpe/v1/genome` which is now the bgz — graph stayed correct.
- **gffread segfaults on bgzipped FASTA input** (verified manually
  inside the Docker image: `gffread … -g foo.fa.gz` → SIGSEGV;
  decompressing to plain `.fa` works). htslib path in gffread is
  unreliable. Worked around in code by `bgzip -d -c` decompressing
  the bgz to a plain `.fa` in the gffread step's work dir, then
  passing the plain path to gffread. Bucket still holds bgz triplet
  for the API runtime.
- Reuse logic added: gffread step skips re-downloading the genome
  triplet if all three files are already on disk at the bgz-fai
  step's work dir (so a single `kb build` doesn't round-trip the
  bucket twice).
- Followed-up open question: `main.py:222` still has
  `if asset_id == "betpe/v1/genome": fetch_betpe_genome(...)` from
  the old `kb sync` dispatch — `betpe/v1/genome` is now the derived
  bgz, not the source. Mooted by the refactor below.

#### Big realisation today: only derived assets belong in the bucket

While debugging the above, the architecture-level problem became
obvious. Every external source we touch needs *some* preprocessing —
`lcl|` strip on the betpe genome, sort on gffs, bgzip+faidx on
fastas, etc. So the source/derived split that `kb sync` was built
around is artificial:

- We end up storing redundant blobs in the bucket (raw `.fa` AND
  bgz of the same content).
- The build step round-trips: download raw → process → upload
  derived → re-download derived → decompress for gffread → ...
- `kb sync` exists to upload raw sources to the bucket, but those
  raw sources are never actually consumed as-is — they go straight
  into a build step. The intermediate bucket presence buys nothing.

The cleaner model (next-session refactor target):

- **Only derived `Asset` nodes exist** in the graph and in the bucket.
  No `genome-source` / `gff-source` etc.
- **`source_url:` lives on the derived `Asset`** that is the
  primary output of a step (e.g., `betpe/v1/genome` is the bgz, and
  carries `source_url: https://genomevolution.org/coge/…`).
- **BuildStep has no `reads:` for raw URL inputs** — the URL is
  implicit on the write target. `reads:` still exists for
  upstream-derived inputs (e.g., the gffread step `reads:`
  the bgz `genome` Asset that a previous step produced).
- **The build function** looks up its primary write target's
  `source_url`, streams from URL with `httpx`, processes in a
  temp dir, uploads to the bucket via `object:`, discards the temp.
- **`kb sync` goes away.** `kb build` is the whole flow.
  One-shot source uploads we did to bootstrap the bucket stay there
  but stop being graph-modelled.

Worked example for betpe:

```yaml
# under taxa: betpe -> assemblies: v1 -> assets:
- name: genome
  format: fasta
  object: Bepen_v1p2_genome.fa.gz
  source_url: https://genomevolution.org/coge/api/v1/genomes/68624/sequence
- name: genome-fai
  format: fai
  object: Bepen_v1p2_genome.fa.gz.fai
- name: genome-gzi
  format: gzi
  object: Bepen_v1p2_genome.fa.gz.gzi
```

```yaml
# under steps:
- id: betpe/v1/build-genome-bgz-fai
  writes:
    - id: betpe/v1/genome
    - id: betpe/v1/genome-fai
    - id: betpe/v1/genome-gzi
```

Build function:

```python
def build_betpe_v1_genome_bgz_fai(client, container, assets):
    # assets["betpe/v1/genome"].source_url is the COGE URL
    # stream → temp → sed lcl| strip → bgzip → samtools faidx
    # → client.upload(...) of the bgz triplet
    # → done; no kb sync, no genome-source asset, no raw .fa in bucket
```

Same pattern applies to any source needing prep:

- gffs that need sorting → a `build-gff-sorted` step fetches the
  raw gff from `source_url`, sorts, bgzips, uploads.
- eggnog tsvs that need column normalisation → same shape.

#### Next-session work (start here)

1. **Prototype the derived-only model on betpe genome.**
   - yaml: drop `genome-source`, move `source_url:` onto the
     existing `genome` derived Asset.
   - yaml: drop `reads:` from `betpe/v1/build-genome-bgz-fai`.
   - main.py: rewrite `build_betpe_v1_genome_bgz_fai` to look up
     `genome.source_url` from yaml/graph and stream via `httpx`
     instead of `client.download_object`. Discard the temp at end.
   - Bucket cleanup: delete `Bepen_v1p2_genome.fa` (the raw `.fa`).
   - Confirm `kb build` still produces the bgz triplet and the
     downstream gffread step still works.

2. **Decide how the build function gets access to its outputs'
   `source_url`.** Options:
   - Pass the yaml/Asset-record dict into the function alongside
     `(client, container)`. Simplest.
   - Pre-resolve URLs and pass just the URL string per write id.
   - Have the function read `knowledge.yaml` itself.
   Pick one and apply across.

3. **Kill `kb sync`.** Once (1) is proven, delete the `sync`
   subcommand, `fetch_<species>_genome` functions, and the
   `SYNC_REQUIRED_ENV` env-var split. `kb build` is the only
   subcommand.

4. **Apply the pattern to the remaining genomes.** arath / potra /
   pruav each get a `build-<taxon>-<v>-genome-bgz-fai` step that
   fetches from `source_url`, possibly preprocesses, bgzips,
   uploads. picab / pinsy already have a clean bgz in the bucket
   from out-of-band upload — decide whether to retroactively model
   them with a build step (no `source_url` they were uploaded from
   local) or leave them as bucket-only Assets with no step.

5. **Apply the pattern to gffs that need preprocessing.** Most/all
   gffs in the bucket are pre-sorted versions; model them as
   derived outputs of a `build-gff-sorted` step rather than raw
   sources.

6. **Then resume the gffread / BLAST / DIAMOND replication across
   the other 6 annotations.** Same plan as before, just on top of
   the new model.

7. **Build manifest / staleness — DEFER.** Unchanged.

#### Open questions for the new session

- How does the build function get its outputs' `source_url`? See
  next-session step (2).
- picab / pinsy modelling: their bgz was uploaded out-of-band from
  local copies (no `source_url`). Model them as build-stepless
  derived Assets, or invent a no-op step for graph symmetry?
- Object naming for derived gffread outputs across multi-annotation
  taxa (arath has two annotations under the same assembly) — still
  open from before.
- Does the API runtime read FASTA/index files directly from bucket
  via htslib (HTTPS-aware) or expect a local mount? Affects whether
  hosts running the API need a pull step.
- Sequences-in-graph alternative (`Cds` / `Transcript` / `Protein`
  nodes with sequence properties) raised in a prior session;
  deferred in favour of bucket+faidx for now.
- gffread can't read bgz FASTA without segfaulting — the current
  decompress-before-call workaround stays for now. The user
  floated writing a bespoke `(genome+gff) -> (cds, mrna, protein)`
  extractor; revisit if gffread becomes more annoying.

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
- **betpe genome FASTA headers carry a `lcl|` BLAST prefix**
  (`>lcl|Contig0` etc.) but the gff references bare names
  (`Contig0`). `build_betpe_v1_v1_2_gffread` strips `>lcl|` → `>`
  inline as a workaround. Real fix is to re-upload the genome
  without the prefix.
- **betpe gff has duplicate mRNA features** with the same id,
  surfacing as `Error: discarding overlapping duplicate mRNA feature`
  from gffread and `[W::fai_insert_index] Ignoring duplicate sequence`
  from `samtools faidx` on the derived FASTAs. Non-fatal. Other
  taxa's gffs may have the same — watch for it.

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
- The image's `appuser` is created with `--create-home` (not
  `--no-create-home`); DuckDB auto-installs the `httpfs` extension at
  runtime and needs a writable `$HOME` for its extension cache.
- `kb build` in the container needs three mounts: `.env.shared`,
  `.env`, and `/opt/neo4j/import` (read-write — DuckDB writes CSVs
  there and neo4j reads via its own `:ro` mount). Plus
  `--network <compose-network>` to reach the neo4j service by name.
