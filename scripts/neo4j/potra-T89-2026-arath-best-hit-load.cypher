// BEST_ARABIDOPSIS_HIT relationships for the T89 haplotypes, Gene -> arath Gene.
//
// Requires potra-T89-2026-load.cypher and the arath-araport11 gene load to
// have run first. CSVs come from
// scripts/duckdb/generate-potra-T89-2026-arath-best-hits.sql.
//
// The arath target has to be scoped: arath-tair10 carries the same AT
// identifiers as arath-araport11, so an unscoped match would create an edge
// to each. The scope is a WHERE check rather than a pattern, so the match
// stays an index seek on gene_id instead of expanding every HAS_GENE edge
// out of the arath annotation for each row.
//
// The organelle genes are single nodes shared by both haplotypes, so their
// edges are loaded once, reached through h1. The per-haplotype clear steps
// exclude them for the same reason.

// potra-T89-2026-h1
MATCH (:Annotation {id: 'potra-T89-2026-h1'})-[:HAS_GENE]->(g:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
WHERE NOT g.chromosome IN ['pt', 'mt']
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h1'})
MATCH (arath:Annotation {id: 'arath-araport11'})
CALL (a, arath) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-h1-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  WHERE (arath)-[:HAS_GENE]->(t)
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// potra-T89-2026-h2
MATCH (:Annotation {id: 'potra-T89-2026-h2'})-[:HAS_GENE]->(g:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
WHERE NOT g.chromosome IN ['pt', 'mt']
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h2'})
MATCH (arath:Annotation {id: 'arath-araport11'})
CALL (a, arath) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-h2-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  WHERE (arath)-[:HAS_GENE]->(t)
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// Organelles, shared by both haplotypes
MATCH (g:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
WHERE g.id STARTS WITH 'T89pt' OR g.id STARTS WITH 'T89mt'
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h1'})
MATCH (arath:Annotation {id: 'arath-araport11'})
CALL (a, arath) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-organelle-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  WHERE (arath)-[:HAS_GENE]->(t)
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification - expect 29439 and 29280
MATCH (a:Annotation)-[:HAS_GENE]->(:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
WHERE a.id STARTS WITH 'potra-T89-2026'
RETURN a.id AS annotation, count(r) AS hits
ORDER BY annotation;
