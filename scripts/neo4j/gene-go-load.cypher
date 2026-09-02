// HAS_GO_TERM relationships, Gene -> GoTerm, resolving alt-ids via GoAlias.
//
// Requires go-load.cypher and gene-load.cypher to have run first.
//
// arath is omitted: no gene-go CSVs were generated for it.

// betpe-v1.2
MATCH (:Annotation {id: 'betpe-v1.2'})-[:HAS_GENE]->(:Gene)-[r:HAS_GO_TERM]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'betpe-v1.2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///betpe-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// picab-v2.0
MATCH (:Annotation {id: 'picab-v2.0'})-[:HAS_GENE]->(:Gene)-[r:HAS_GO_TERM]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'picab-v2.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// pinsy-v1.0
MATCH (:Annotation {id: 'pinsy-v1.0'})-[:HAS_GENE]->(:Gene)-[r:HAS_GO_TERM]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'pinsy-v1.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// potra-v2.2
MATCH (:Annotation {id: 'potra-v2.2'})-[:HAS_GENE]->(:Gene)-[r:HAS_GO_TERM]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-v2.2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// pruav-v2.0
MATCH (:Annotation {id: 'pruav-v2.0'})-[:HAS_GENE]->(:Gene)-[r:HAS_GO_TERM]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'pruav-v2.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///pruav-gene-go.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  OPTIONAL MATCH (direct:GoTerm {id: row.go_id})
  OPTIONAL MATCH (:GoAlias      {id: row.go_id})-[:IS_ALIAS_OF]->(viaAlias:GoTerm)
  WITH g, coalesce(direct, viaAlias) AS goterm
  WHERE goterm IS NOT NULL
  CREATE (g)-[:HAS_GO_TERM]->(goterm)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification - per-annotation gene and HAS_GO_TERM counts
MATCH (a:Annotation)-[:HAS_GENE]->(g:Gene)
OPTIONAL MATCH (g)-[r:HAS_GO_TERM]->()
RETURN a.id AS annotation, count(DISTINCT g) AS geneCount, count(r) AS hasGoTermCount
ORDER BY annotation;
