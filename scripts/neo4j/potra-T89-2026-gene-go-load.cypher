// HAS_GO_TERM relationships for the T89 haplotypes, Gene -> GoTerm,
// resolving alt-ids via GoAlias.
//
// Requires go-load.cypher and potra-T89-2026-load.cypher to have run first.
// CSVs come from scripts/duckdb/generate-potra-T89-2026-gene-go.sql.
//
// The organelle genes are single nodes shared by both haplotypes, so their
// edges are loaded once, reached through h1. The per-haplotype clear steps
// exclude them for the same reason.

// potra-T89-2026-h1
MATCH (:Annotation {id: 'potra-T89-2026-h1'})-[:HAS_GENE]->(g:Gene)-[r:HAS_GO_TERM]->()
WHERE NOT g.chromosome IN ['pt', 'mt']
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h1'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-h1-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// potra-T89-2026-h2
MATCH (:Annotation {id: 'potra-T89-2026-h2'})-[:HAS_GENE]->(g:Gene)-[r:HAS_GO_TERM]->()
WHERE NOT g.chromosome IN ['pt', 'mt']
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-h2-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// Organelles, shared by both haplotypes
MATCH (g:Gene)-[r:HAS_GO_TERM]->()
WHERE g.id STARTS WITH 'T89pt' OR g.id STARTS WITH 'T89mt'
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h1'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-organelle-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification
MATCH (a:Annotation)-[:HAS_GENE]->(:Gene)-[r:HAS_GO_TERM]->()
WHERE a.id STARTS WITH 'potra-T89-2026'
RETURN a.id AS annotation, count(r) AS goEdges
ORDER BY annotation;
