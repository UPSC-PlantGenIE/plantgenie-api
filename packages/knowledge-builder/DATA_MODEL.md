# Knowledge graph data model

The graph has two halves that meet:

1. **Domain nodes** — the biological facts: what organism, which genome
   assembly, which annotation. These already exist (or are being created) in a
   parallel line of work as the application's UI is rebuilt.
2. **Build nodes** — the provenance/lineage layer: the data files (`Asset`)
   and the processes that produce derived files from other files
   (`BuildStep`). This is what `knowledge-builder` manages.

Two directional conventions, one per half:

- **Domain + bridge edges (`OF`, `FROM`)** point toward what a node *belongs
  to* — upward, toward the root `Taxon`.
- **Build edges (`READ_BY`, `WRITES`)** point the way *data flows* — from
  source files, through steps, to derived outputs.

A third layer, the **application graph** (`Gene`, `GoTerm`, …), is loaded from
the build half's outputs and hangs off the domain nodes.

---

## Domain nodes

### Taxon
The foundational unit. All other data depends on a `Taxon`. For any data to
enter the application, a `Taxon` must already exist or be created first.

### Assembly
Marks that a genome assembly was produced for a `Taxon`. Has a `version`. A
`Taxon` can have multiple assemblies (e.g. re-sequenced and re-assembled with
newer technology).

### Annotation
Marks that an `Assembly` was annotated — gene models, functional descriptions,
etc. An `Assembly` can have multiple annotations (e.g. different prediction
tools).

---

## Domain edges

The desired flow is `Annotation → Assembly → Taxon` (each node points at the
thing it depends on). A single `OF` edge type covers both levels — it reads as
a noun phrase in the arrow direction and the node labels carry the specificity:

| Edge | Meaning |
|---|---|
| `(:Annotation)-[:OF]->(:Assembly)` | this annotation was produced for that assembly |
| `(:Assembly)-[:OF]->(:Taxon)` | this assembly was produced for that taxon |

This replaces the earlier `HAS_ASSEMBLY` name, which only read correctly in the
opposite direction (`Taxon → Assembly`) and was being reused for two different
edges. Reusing one `OF` type loses nothing: `MATCH (:Annotation)-[:OF]->(:Assembly)`
is just as precise as a named edge because the endpoints disambiguate it.

---

## Build nodes

### Asset
A data source — a file. Examples for betula pendula: the GFF from CoGe, the
genome FASTA, the eggnog annotation TSV, and derived CSVs.

Assets are deliberately uniform: the same node type whether the file is a
source or an output, and whether it's a FASTA, GFF, TSV, or CSV. The specifics
live in **properties** rather than labels or edge types — e.g.
`format: fasta | gff | tsv | csv | json`, plus storage info
(`bucket_uri`, `source_url?`). This keeps an asset free to attach to either an
`Assembly` or an `Annotation` and to be consumed/produced by any `BuildStep`.

An asset's nature is **read from the graph, not declared**:

- **Source asset** — no `BuildStep` `WRITES` it. It simply exists (someone
  uploaded it, or it was fetched from an external URL).
- **Derived asset** — some `BuildStep` `WRITES` it, and therefore it depends on
  that step's inputs.

### BuildStep
A process that produces one or more derived assets from one or more inputs. A
`BuildStep` always has at least one incoming `READ_BY` edge — it needs a data
source — and produces output via `WRITES`.

---

## Build edges

| Edge | Meaning |
|---|---|
| `(:Asset)-[:READ_BY]->(:BuildStep)` | the step consumes this asset as input (the asset must already exist) |
| `(:BuildStep)-[:WRITES]->(:Asset)` | the step produces this (derived) asset |

Both edges flow in the direction the data moves:

```
source Asset ─[:READ_BY]→ BuildStep ─[:WRITES]→ derived Asset
```

Following the arrows forward runs the pipeline in order (a topological walk);
following them backward from a derived asset walks its full lineage to the
sources it came from.

---

## Bridge edge — joining the two halves

An `Asset` is tied to the domain entity it originates from by a `FROM` edge:

| Edge | Meaning |
|---|---|
| `(:Asset)-[:FROM]->(:Assembly)` | this file (e.g. a genome FASTA) comes from that assembly |
| `(:Asset)-[:FROM]->(:Annotation)` | this file (e.g. a GFF or eggnog TSV) comes from that annotation |

`FROM` is kept distinct from `OF`: `OF` is the domain hierarchy
(`Annotation → Assembly → Taxon`), while `FROM` says which domain entity a
data file belongs to.

Only **source** assets carry `FROM`. A **derived** asset gets no `FROM` edge —
its domain membership is recovered by walking lineage backward
(`derived ← WRITES ← BuildStep ← READ_BY ← source ─FROM→ domain`). This avoids a
`FROM` that could drift out of sync with what the asset is actually built from,
or become ambiguous when a step reads sources from more than one domain entity.

---

## Identifiers

Every node has a string `id`. Ids are path-shaped, using `/` as a separator,
and encode the node's place in the domain hierarchy.

| Node | Example id |
|---|---|
| Taxon | `betpe` |
| Assembly | `betpe/v1` |
| Annotation | `betpe/v1/v1.2` |
| Source asset (annotation-level) | `betpe/v1/v1.2/gff` |
| Source asset (assembly-level) | `betpe/v1/genome` |
| BuildStep | `betpe/v1/v1.2/build-gene-records` |
| Derived asset | `betpe/v1/v1.2/gene-records` |
| LoadStep | `betpe/v1/v1.2/load-gene-records` |

Two conventions are baked in:

- **Path encodes the domain hierarchy.** The slashes before the final segment
  trace the `OF` / `FROM` chain, so a node's id alone tells you which taxon,
  assembly, and annotation it belongs to. The Swift bucket layout is intended
  to mirror this path eventually (today it doesn't; see open questions).
- **Verb prefix on steps, noun on assets.** `build-` and `load-` mark step
  ids; assets have no prefix. This lets a step and its sole output share a
  noun without colliding (`build-gene-records` writes `gene-records`). Node
  labels disambiguate types in queries; the prefixes disambiguate visually.

Domain-free source assets (e.g. a GO ontology file) and cross-taxon derived
assets don't yet have a settled id form. See open questions.

---

## Load nodes

### LoadStep
A step whose effect is graph state rather than a file. A `LoadStep` reads one
or more source `Asset`s (typically derived CSVs from `BuildStep`s, sometimes
a domain-free source like an ontology file) and creates application-graph
nodes/edges directly in Neo4j.

`LoadStep` is deliberately a distinct node type from `BuildStep`:

- **Different output.** It ends in graph state, not in a derived `Asset`.
  There is no outgoing `WRITES` edge.
- **Different dependencies.** It can depend on the *graph state* another
  load left behind, which `BuildStep`s never do.

Its only edge into the build half is the same incoming `READ_BY` that
`BuildStep` uses.

| Edge | Meaning |
|---|---|
| `(:Asset)-[:READ_BY]->(:LoadStep)` | the load consumes this asset as input |

---

## Load ordering — `REQUIRES`

Some loads depend on the graph state another load already produced. For
example, the gene↔GO load needs `Gene` nodes (from the gene-records load)
and `GoTerm` nodes (from a GO ontology load) to exist. There's no shared
`Asset` to express that dependency through, so a direct edge does the job:

| Edge | Meaning |
|---|---|
| `(:LoadStep)-[:REQUIRES]->(:LoadStep)` | the source load must have run first |

`REQUIRES` belongs to the dependency-direction edge family, alongside `OF`
and `FROM`; it points at what is depended on. The build-half edges
(`READ_BY`, `WRITES`) point along data flow because there are bytes moving
between steps. `REQUIRES` has no bytes, just a precondition, so the
data-flow convention doesn't apply.

`REQUIRES` is strictly for LoadStep → LoadStep ordering, and only when the
dependency is graph state, i.e. nodes or edges a previous load created in
Neo4j. A `LoadStep`'s ordering relative to the `BuildStep`(s) producing its
inputs is already handled by `READ_BY` / `WRITES`, the same as for any
other consumer.

---

## Loaded entities (the application graph)

A third layer of nodes (`Gene`, `GoTerm`, and other features) is what the
application actually queries. They are **not** `Asset`s; they are loaded
into Neo4j from the build half's derived outputs by `LoadStep`s.

A `BuildStep` is format- and method-agnostic: it takes input Asset(s) in
whatever form and produces output Asset(s). *How* (which tool, which file
format) is an instance detail, not part of the model. That said, data
destined for the application side will **almost always** arrive via a
`BuildStep` that `WRITES` a CSV, which a `LoadStep` then imports into Neo4j
with Cypher.

### Gene
Loaded from an annotation's derived `Asset` (gene models). A `Gene` attaches
**directly to its `Annotation`**, a single hop that keeps application
entities on the domain nodes rather than on build artifacts. Edge name and
direction should match whatever convention the application graph already
uses.

### GoTerm
A **global, taxon-independent** ontology, with the same terms applying
across every annotation. Loaded from its own source `Asset` (an ontology
file), independent of any annotation; the derived GO `Asset`s therefore
carry no `FROM`.

### Gene → GoTerm
The gene↔GO-term link is annotation-specific, but its **origin is open**:
it may come from any tool, or from manual curation. Whatever the source, a
`BuildStep` parses it into an `Asset` that carries the mapping, and a
`LoadStep` establishes the relationship. That `LoadStep` `REQUIRES` both
the gene-records load (so `Gene` nodes exist) and the GO ontology load (so
`GoTerm` nodes exist); neither dependency is via a shared `Asset`.

---

## Worked example (betula pendula)

Domain:

```
(ann:Annotation {id: "betpe/v1/v1.2"})-[:OF]->(asm:Assembly {id: "betpe/v1"})-[:OF]->(:Taxon {id: "betpe"})
```

Build. Source assets attach to the domain via `FROM`; derived assets come
out of steps:

```
(genome:Asset {id: "betpe/v1/genome",      format: "fasta"})-[:FROM]->(asm)
(gff:Asset    {id: "betpe/v1/v1.2/gff",    format: "gff"})  -[:FROM]->(ann)
(eggnog:Asset {id: "betpe/v1/v1.2/eggnog", format: "tsv"})  -[:FROM]->(ann)

(gff)   -[:READ_BY]->(recstep:BuildStep {id: "betpe/v1/v1.2/build-gene-records"})
(eggnog)-[:READ_BY]->(recstep)
(recstep)-[:WRITES]->(records:Asset {id: "betpe/v1/v1.2/gene-records", format: "csv"})

(gff)   -[:READ_BY]->(gostep:BuildStep {id: "betpe/v1/v1.2/build-gene-go"})
(eggnog)-[:READ_BY]->(gostep)
(gostep)-[:WRITES]->(gene_go:Asset {id: "betpe/v1/v1.2/gene-go", format: "csv"})
```

Load. Derived CSVs are imported into the application graph by `LoadStep`s:

```
(records)-[:READ_BY]->(recload:LoadStep {id: "betpe/v1/v1.2/load-gene-records"})
(gene_go)-[:READ_BY]->(goload:LoadStep  {id: "betpe/v1/v1.2/load-gene-go"})
(goload)-[:REQUIRES]->(recload)   # Gene nodes must exist before :HAS_GO edges
```

The gene↔GO load will gain a second `REQUIRES` once the GO ontology load
exists in the catalog.

---

## Open questions

1. **BuildStep cardinality.** Is "≥1 `READ_BY` and ≥1 `WRITES`" a hard
   invariant we enforce, or just the common case? (`LoadStep` already covers
   the "no `WRITES`" case by being a separate node type, so this is now only
   about `BuildStep`.)
2. **Asset and step properties.** Beyond `format`, `bucket_uri`, and
   `source_url?`, what else does an `Asset` carry? And what's on a
   `BuildStep` / `LoadStep` (`command`, the SQL/Cypher body, a checksum of
   it)?
3. **Domain-free source assets.** Ontologies (GO, PO, etc.) and reference
   databases (e.g. a UniRef DB for DIAMOND) belong to no taxon. Where do
   they live in `knowledge.yaml`, and what id form do they take? A top-level
   `shared:` block with ids like `shared/go-basic` is one candidate.
4. **Cross-taxon derived assets.** DIAMOND hits between two taxa, ortholog
   groups, synteny blocks; assets that originate from more than one taxon.
   They don't have a single `FROM` target, and their id has no single
   domain path. Convention not yet decided.
