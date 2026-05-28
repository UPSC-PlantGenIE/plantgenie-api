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

## Loaded entities (the application graph)

A third layer of nodes — `Gene`, `GoTerm`, and other features — is what the
application actually queries. They are **not** `Asset`s; they are loaded into
Neo4j from the build half's derived outputs. Exactly how that loading step fits
the `BuildStep` model — in particular whether it writes anything — is still
open (see open question #1).

A `BuildStep` is format- and method-agnostic: it takes input Asset(s) in
whatever form and produces output Asset(s). *How* — which tool, which file
format — is an instance detail, not part of the model. That said, data destined
for the application side will **almost always** arrive via a `BuildStep` that
`WRITES` a CSV, which a load step then imports into Neo4j with Cypher.

### Gene
Loaded from an annotation's derived `Asset` (gene models). A `Gene` attaches
**directly to its `Annotation`** — a single hop, and it keeps application
entities on the domain nodes rather than on build artifacts. Edge name and
direction should match whatever convention the application graph already uses.

### GoTerm
A **global, taxon-independent** ontology — the same terms apply across every
annotation. Loaded from its own source `Asset` (an ontology file), independent
of any annotation; the derived GO `Asset`s therefore carry no `FROM`.

### Gene → GoTerm
The gene↔GO-term link is annotation-specific, but its **origin is open** — it
may come from any tool, or from manual curation. Whatever the source, a
`BuildStep` parses it into an `Asset` that carries the mapping, and a load step
establishes the relationship. That load needs *both* the mapping `Asset` *and*
the `GoTerm` nodes already present — so it depends on another load step's graph
state, not just on a shared `Asset` (see open question #1).

---

## Worked example (betula pendula) — tentative

Domain:

```
(ann:Annotation)-[:OF]->(asm:Assembly {version: "v1.2"})-[:OF]->(:Taxon {name: "Betula pendula"})
```

Build — source assets attach to the domain via `FROM`; derived assets come out
of steps:

```
(genome:Asset {format: "fasta"})-[:FROM]->(asm)    # source, from CoGe
(gff:Asset    {format: "gff"})  -[:FROM]->(ann)    # source, from CoGe
(eggnog:Asset {format: "tsv"})  -[:FROM]->(ann)    # source, on Swift

(gff)   -[:READ_BY]->(recstep:BuildStep {id: "betpe-gene-records"})
(eggnog)-[:READ_BY]->(recstep)
(recstep)-[:WRITES]->(records:Asset {format: "csv"})   # derived, no FROM

(gff)   -[:READ_BY]->(gostep:BuildStep {id: "betpe-gene-go"})
(eggnog)-[:READ_BY]->(gostep)
(gostep)-[:WRITES]->(gene_go:Asset {format: "csv"})    # derived, no FROM
```

---

## Open questions

1. **Ordering that isn't via a shared `Asset`.** A load step can depend on the
   graph state left by an earlier load step (e.g. `GoTerm` nodes must exist
   before the gene↔GO link is established), even though the two steps share no
   `Asset`. How does the build DAG represent that kind of ordering? (Related:
   steps that `WRITES` into Neo4j rather than into an `Asset` file.)
2. **BuildStep cardinality.** Is "≥1 `READ_BY` and ≥1 `WRITES`" a hard invariant
   we enforce, or just the common case?
3. **Asset properties.** Beyond `format`, `bucket_uri`, and `source_url?`, what
   else does an `Asset` carry? And what's on a `BuildStep` (`command`, the
   SQL/Cypher body, a checksum of it)?
