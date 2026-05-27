# knowledge-builder

A graph-driven build system for the PlantGenie data layer. Build steps and
their inputs/outputs live as nodes in the same Neo4j instance that holds the
application graph. A Typer CLI walks the dependency graph, detects which
upstream sources have changed in the Swift bucket, and re-runs only the
downstream steps that need it.

## Goal

Reproducibility for everything we feed into Neo4j: GFFs, FASTAs, eggnog
annotations, derived sequences (CDS / mRNA / protein), DIAMOND databases,
pairwise DIAMOND hits, the GO ontology graph, gene→GO closures, and every
CSV the application currently consumes. Each artefact has a known producer,
a known set of inputs, and a known checksum. Update an upstream → the runner
knows what downstream is stale.

## Scope of v1

In:

- Catalog of every existing artefact the app already depends on (the ~17 DuckDB
  `COPY` blocks in `generate-neo4j-records.sql` and the ~15 Cypher load blocks
  in `neo4j-queries.cypher`, each lifted into its own `BuildStep`).
- The GO ancestor-closure rewrite (Python + networkx) as a new `BuildStep`.
- `kb bootstrap` / `kb sync` / `kb status` / `kb build` / `kb logs` Typer
  subcommands.
- Swift as the storage backend (`packages/shared` swift client, extended if
  needed for HEAD/ETag lookups without breaking existing callers).
- Checksum-based staleness via Swift `ETag` headers.
- Structured JSON logging captured per `BuildRun`, log files uploaded to the
  bucket alongside the artefacts.

Deferred:

- Parallel execution (the dependency graph makes ordering non-trivial; serial
  is fine for v1).
- A UI dashboard for visualising graph status and clicking through to a
  step's outputs and logs. Logging shape is chosen now so this can be added
  later without re-instrumenting.
- Python entrypoint–style step bodies for type-checked inputs/outputs.
  Everything is a shell string for v1.
- Retry / partial-failure recovery. Failed steps stay failed until re-run.

## Schema

Two concerns live as separate node families so that catalog redefinition does
not destroy runtime history.

### Catalog nodes (static; rewritten by `kb bootstrap`)

- `(:DataAsset {id, kind, bucket_uri, source_url?, description?})`
  - `id` is the stable business key (e.g. `pinsy::gff`,
    `pinsy::gene-records-csv`, `go::basic-json`).
  - `kind` is a free-form string. Initial values: `gff`, `fasta`, `cds_fasta`,
    `mrna_fasta`, `protein_fasta`, `eggnog_tsv`, `diamond_db`, `diamond_hits`,
    `go_basic_json`, `go_terms_csv`, `go_aliases_csv`, `go_edges_csv`,
    `gene_records_csv`, `gene_go_csv`, `functional_descriptions_txt`.
  - `bucket_uri` is the canonical Swift URL.
  - `source_url` is set only on upstream assets the project does not produce
    (e.g. `https://current.geneontology.org/ontology/go-basic.json`).
- `(:BuildStep {id, command, script_sha?, body_path?})`
  - `id` is the stable business key (e.g. `pinsy-gene-records`,
    `go-load-terms`).
  - `command` is a shell string that the runner will exec. Examples:
    - `kb run-sql steps/sql/pinsy-gene-records.sql`
    - `kb run-cypher steps/cypher/load-go-terms.cypher`
    - `python -m knowledge_builder.steps.build_go_closure --species pinsy`
    - `gffread {{ inputs.gff.local }} -g {{ inputs.fasta.local }} -x {{ outputs.cds.local }}`
  - `body_path` (optional) records the snippet file the command consumes so
    `script_sha` can be tracked for staleness.

### Edges (catalog)

- `(:BuildStep)-[:READS {role}]->(:DataAsset)` — input. `role` names the input
  (`gff`, `eggnog`, `fasta`, …) so the runner can resolve `{{ inputs.gff }}`
  in templates.
- `(:BuildStep)-[:WRITES {role}]->(:DataAsset)` — output, same convention.
- `(:Annotation)-[:HAS_FILE {role}]->(:DataAsset)` /
  `(:Assembly)-[:HAS_FILE {role}]->(:DataAsset)` — the bridge into the
  existing application graph. Lets a future query ask "what is the GFF for
  picab-v2.0?" without leaving Neo4j.

### Runtime nodes (mutable; written by the runner, **not** dropped on bootstrap)

- `(:BuildRun {id, step_id, started_at, finished_at, status, exit_code,
  log_uri, input_checksums, output_checksums})`
  - `step_id` is the business-key reference to a `BuildStep.id`. Linked
    structurally via `(:BuildRun)-[:OF_STEP]->(:BuildStep)`, but the property
    also exists so history survives a catalog re-bootstrap where a step is
    temporarily missing.
  - `status` ∈ `running` | `success` | `failed`.
  - `input_checksums` / `output_checksums` are JSON maps of role → checksum
    at the time of the run. Enables "what changed since last successful run".
  - `log_uri` points to the JSON log file uploaded to the bucket.
- `(:DataAsset)` runtime properties, updated in place by `kb sync` and after
  successful `BuildRun`s: `checksum`, `checksum_algo`, `size_bytes`,
  `last_synced`, `last_modified` (from Swift).

### Bootstrap behaviour

`kb bootstrap` is a destructive catalog refresh:

1. `MATCH (n:DataAsset) DETACH DELETE n`
2. `MATCH (n:BuildStep) DETACH DELETE n`
3. `CREATE` every `DataAsset`, `BuildStep`, `READS`, `WRITES`, and `HAS_FILE`
   row from the Python catalog in a single UNWIND batch.

No `MERGE`s — they are too slow at this volume. `BuildRun` history is
untouched. After bootstrap the user runs `kb sync` to repopulate checksums on
`DataAsset` nodes (everything is treated as "unknown checksum" → stale until
synced).

The existing `(:Annotation)` and `(:Assembly)` nodes also do not get touched
— bootstrap re-links them by `MATCH` + `CREATE` of the new `HAS_FILE`
edges.

## Catalog definition (Python)

Steps and assets are declared in Python data, not Cypher init files. Example
shape (not final code, just illustrating the contract):

```python
# packages/knowledge-builder/src/knowledge_builder/catalog/__init__.py
pinsy_gff = upstream_asset(
    id="pinsy::gff",
    kind="gff",
    bucket_uri=SWIFT + "/Pinsy01_240308_at01_longest_no_TE.gff3.gz",
)
pinsy_eggnog = upstream_asset(
    id="pinsy::eggnog-panthers",
    kind="eggnog_tsv",
    bucket_uri=SWIFT + "/Pinsy01_240308_..._panthers.tsv.gz",
)
pinsy_gene_records = derived_asset(
    id="pinsy::gene-records-csv",
    kind="gene_records_csv",
    bucket_uri=SWIFT + "/derived/pinsy-gene-records.csv",
)
step(
    id="pinsy-gene-records",
    command="kb run-sql steps/sql/pinsy-gene-records.sql",
    body_path="steps/sql/pinsy-gene-records.sql",
    reads={"gff": pinsy_gff, "eggnog": pinsy_eggnog},
    writes={"records": pinsy_gene_records},
)
```

Catalog declarations may be table-driven (a loop over the seven species is
fine — they do not share output snippets, only the declaration shape). Step
**bodies** (the SQL / Cypher / Python files) are never shared between steps,
even when they look near-identical. Differences are inevitable (betpe's
`m_alias` join, potra's `query` vs pinsy's `id`) and a band-aid in two places
is cheaper than a leaky abstraction.

## Step bodies

Layout under the package:

```
packages/knowledge-builder/src/knowledge_builder/
├── catalog/                     # Python declarations
├── runner/                      # core loop, swift sync, staleness logic
├── cli.py                       # Typer entry point
└── steps/
    ├── sql/                     # one .sql per DuckDB step
    │   ├── pinsy-gene-records.sql
    │   ├── pinsy-gene-go.sql
    │   ├── picab-gene-records.sql
    │   ├── ...
    │   ├── go-terms.sql
    │   ├── go-aliases.sql
    │   └── go-edges.sql
    ├── cypher/                  # one .cypher per Neo4j load step
    │   ├── load-go-terms.cypher
    │   ├── load-go-aliases.cypher
    │   ├── load-go-edges.cypher
    │   ├── load-pinsy-gene-records.cypher
    │   ├── load-pinsy-gene-go.cypher
    │   └── ...
    └── python/                  # python-driven steps
        └── build_go_closure.py  # networkx ancestor closure
```

Bodies are Jinja2-templated with two top-level namespaces:

- `inputs.<role>.local` → local cached path after download from Swift.
- `outputs.<role>.local` → local path the step should write to; the runner
  uploads it after the step finishes.
- `inputs.<role>.bucket_uri` / `outputs.<role>.bucket_uri` are also exposed
  for steps that want to read/write the bucket directly (DuckDB can `read_csv`
  from a Swift URL; that bypass is fine for upstream sources whose
  `local_path` would otherwise be the same gigabytes downloaded twice).

The role names in templates match the `role` properties on `READS` / `WRITES`
edges in the graph.

## Execution model

`kb build <step-id>` (or `kb build --all`):

1. Compute the topological subgraph for the target.
2. For each step in topo order, decide if stale (see below). If not, skip.
3. If stale:
   a. Resolve all `READS` → ensure local cache is up to date (download from
      Swift if missing or checksum mismatch).
   b. Render the `command` with Jinja using the resolved input/output paths.
   c. Create a `BuildRun` node with `status: "running"`.
   d. Exec the command. stdout/stderr go to a JSON log file in a local
      runs/ dir.
   e. On success: upload every `WRITES` artefact to Swift, fetch the new
      ETags, update each `DataAsset` checksum/size/last_modified in place.
   f. Upload the log file to Swift under a runs/ prefix. Stamp the
      `BuildRun` with `status: "success"`, `finished_at`, `exit_code: 0`,
      `output_checksums`, `log_uri`.
   g. On failure: `BuildRun` gets `status: "failed"`, exit code captured,
      partial outputs are **not** uploaded. The runner aborts the topo walk
      so dependents do not run on garbage.

`kb run-sql <path>` / `kb run-cypher <path>` are thin internal subcommands the
runner shells out to from a step's `command`. They:

1. Read `KB_STEP_ID` from env (set by the parent runner).
2. Query Neo4j for that step's `READS` / `WRITES` edges to populate the
   Jinja context.
3. Render the file.
4. Execute via `duckdb` (Python in-process) or via the `neo4j` Python driver.

The `command` shell string is the same contract for everything — direct
binary calls (`gffread`, `diamond`, `bgzip`), `kb run-sql`, `kb run-cypher`,
or `python -m knowledge_builder.steps.build_go_closure`. Steps that need
binaries from `Dockerfile.tools` will be run inside that image; v1 assumes
the user invokes `kb` from inside (or via) a container built on
`Dockerfile.tools` with Python + the package installed on top.

## Staleness rules

A `BuildStep` is stale if **any** of:

- It has no `BuildRun` with `status: "success"`.
- The latest successful `BuildRun.script_sha` differs from the current SHA
  of the file at `body_path` (only checked if `body_path` is set; pure-shell
  steps skip this).
- Any input `DataAsset.checksum` differs from the `input_checksums` recorded
  on the latest successful `BuildRun`.
- Any output `DataAsset.checksum` is null or does not match the bucket's
  current ETag (i.e. the output was deleted or replaced externally).

A `DataAsset` is checked for freshness by `kb sync`, which HEADs every
`bucket_uri` and updates `checksum` / `size_bytes` / `last_modified` if they
have changed. Upstream assets with `source_url` also get an optional HEAD
against the source URL — `kb sync --upstream` will additionally re-download
into the bucket if the source ETag differs, but that is gated behind the
flag because re-downloading multi-GB files is not always wanted.

## Logging

Every `BuildRun` produces a single JSON-lines log file:

```json
{"ts": "...", "level": "info", "event": "step.start", "step_id": "pinsy-gene-records", "run_id": "..."}
{"ts": "...", "level": "info", "event": "input.resolved", "role": "gff", "asset_id": "pinsy::gff", "checksum": "..."}
{"ts": "...", "level": "info", "event": "command.exec", "command": "kb run-sql ..."}
{"ts": "...", "level": "info", "event": "stdout", "line": "..."}
{"ts": "...", "level": "info", "event": "output.uploaded", "role": "records", "asset_id": "pinsy::gene-records-csv", "checksum": "..."}
{"ts": "...", "level": "info", "event": "step.end", "status": "success", "duration_seconds": 12.4}
```

`structlog` configured to emit this format, plus a human-readable mirror to
stderr for terminal use. The log file is uploaded to Swift under
`runs/<step-id>/<run-id>.jsonl` and the `BuildRun.log_uri` field points at
it. The fields chosen here (typed events, stable run/step IDs) are enough to
drive a later UI without reformatting.

## CLI

```
kb bootstrap              # drop+rebuild catalog nodes from the Python catalog
kb sync                   # refresh DataAsset checksums from Swift HEAD
kb sync --upstream        # also re-download upstreams whose source URL ETag changed
kb status [step-id]       # list every step + its staleness, optionally rooted
kb plan <step-id>         # show the topo subgraph that `kb build` would run
kb build <step-id>        # build one step, after building its stale ancestors
kb build --all            # build everything that is stale, topo order
kb logs <run-id>          # stream/fetch a BuildRun's JSON log
kb logs <step-id> --last  # latest log for a step
```

Typer subcommands; all reads from / writes to Neo4j use the `NEO4J_ADDRESS`
/ `NEO4J_USERNAME` / `NEO4J_PASSWORD` env vars already established by
`scripts/check-unresolved-go-ids.sh`. Swift credentials follow the same
env-var pattern (TBD when extending `packages/shared`).

## Migration

1. Bootstrap the catalog from a Python module that enumerates every existing
   artefact: the 17 `COPY` outputs from `generate-neo4j-records.sql`, the
   ~15 `LOAD CSV` blocks from `neo4j-queries.cypher`, the GO graph sources
   (`go-basic.json`), and every upstream GFF / eggnog TSV on Swift.
2. Port each DuckDB `COPY` body to its own `.sql` file under `steps/sql/`,
   with the original `read_csv` / `COPY ... TO` URLs replaced by the Jinja
   `{{ inputs.<role>.local }}` / `{{ outputs.<role>.local }}` placeholders.
3. Port each `LOAD CSV ... CREATE` block to its own `.cypher` file under
   `steps/cypher/`.
4. Add the new `build_go_closure` Python step in place of the existing gene→GO
   COPYs. Its `READS` are each species' eggnog TSV + `go-basic.json`; its
   `WRITES` are the per-species `*-gene-go.csv` files (now closed under
   ancestors). The corresponding `load-<species>-gene-go.cypher` step
   consumes those CSVs unchanged from how it does today, except that the
   set of GO IDs per gene is now connected to the root.
5. Verify parity: each output CSV produced by `kb build --all` is byte-equal
   (or row-set-equal modulo ordering) to the current
   `generate-neo4j-records.sql` output. After parity is confirmed, delete
   `generate-neo4j-records.sql` and `neo4j-queries.cypher` from the repo
   root.

## Open questions to settle during implementation

- Should `(:DataAsset)` get a `version` property derived from the bucket
  ETag, so application queries can pin a specific snapshot? Probably yes,
  but deferred until a consumer needs it.
- Where in the package layout do upstream-source-URL HEAD requests live —
  inside the shared swift client (broader contract) or local to the
  runner? Lean local for v1, lift later if reused.
- How does `kb build` behave if a step's local cache dir is already
  populated with stale outputs from an aborted prior run? Wipe on start vs
  reuse vs error out. Lean wipe on start (simplest, no orphaned bytes).
- DIAMOND pairwise hits: many-to-many between annotations. Each pair is its
  own `BuildStep`? Or one step that produces N×N outputs? Lean one step per
  pair so a single failure doesn't redo the rest.
