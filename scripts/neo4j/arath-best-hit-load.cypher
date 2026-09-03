// BEST_ARABIDOPSIS_HIT relationships, Gene -> arath Gene.
//
// Requires gene-load.cypher to have run first, including the arath-araport11
// block, and the *-arath-best-hits.csv files produced by
// scripts/duckdb/arath-best-hits.sql.
//
// The source gene is matched through its annotation; the arath target is
// matched straight on the gene_id index, since Araport11 AT identifiers only
// occur in that one annotation.

// betpe-v1.2
MATCH (:Annotation {id: 'betpe-v1.2'})-[:HAS_GENE]->(:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'betpe-v1.2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///betpe-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// picab-v2.0
MATCH (:Annotation {id: 'picab-v2.0'})-[:HAS_GENE]->(:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'picab-v2.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// pinsy-v1.0
MATCH (:Annotation {id: 'pinsy-v1.0'})-[:HAS_GENE]->(:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'pinsy-v1.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// potra-v2.2
MATCH (:Annotation {id: 'potra-v2.2'})-[:HAS_GENE]->(:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'potra-v2.2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// pruav-v2.0
MATCH (:Annotation {id: 'pruav-v2.0'})-[:HAS_GENE]->(:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
CALL (r) { DELETE r } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:Annotation {id: 'pruav-v2.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///pruav-arath-best-hits.csv' AS row
  FIELDTERMINATOR '\t'
  MATCH (a)-[:HAS_GENE]->(g:Gene {id: row.gene_id})
  MATCH (t:Gene {id: row.arath_gene_id})
  CREATE (g)-[:BEST_ARABIDOPSIS_HIT {
    evalue: toFloat(row.evalue),
    bitscore: toFloat(row.bitscore)
  }]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification - expect 22485, 30702, 32255, 29601, 24679
MATCH (a:Annotation)-[:HAS_GENE]->(g:Gene)-[r:BEST_ARABIDOPSIS_HIT]->()
RETURN a.id AS annotation, count(r) AS bestHitCount
ORDER BY annotation;
