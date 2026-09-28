// Coexpression edges for picab-v2.0-cold-roots.
//
// Requires annotation-load.cypher and gene-load.cypher to have run first.
// Needs picab-cold-roots-coexpression.csv in /opt/neo4j/import. That file
// carries both metrics; the -pearson and -spearman files are subsets of it
// and the -1/-2/-3 files are chunks of it.
//
// One edge per pair, stored gene_a -> gene_b. Queries ignore direction with
// (g)-[r:COEXPRESSED_WITH]-(other). The experiment is a property, so a
// second experiment's edges can sit alongside these and be filtered on it.
//
// Gene matches seek on the gene_id index, then check HAS_GENE in a WHERE.
// LOAD CSV stays outside the subquery so IN TRANSACTIONS batches CSV rows.

MATCH (a:Annotation {id: 'picab-v2.0'})-[:HAS_GENE]->()-[r:COEXPRESSED_WITH]->()
WHERE r.experiment = 'picab-v2.0-cold-roots'
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///picab-cold-roots-coexpression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (source:Gene {id: row.gene_a})
  WHERE (a)-[:HAS_GENE]->(source)
  MATCH (target:Gene {id: row.gene_b})
  WHERE (a)-[:HAS_GENE]->(target)
  CREATE (source)-[:COEXPRESSED_WITH {
    experiment: 'picab-v2.0-cold-roots',
    pearson:    toFloat(row.pearson),
    spearman:   toFloat(row.spearman)
  }]->(target)
} IN TRANSACTIONS OF 10000 ROWS;

// Verification - expect 2,940,805 edges
MATCH ()-[r:COEXPRESSED_WITH]->()
WHERE r.experiment = 'picab-v2.0-cold-roots'
RETURN count(r) AS edges;
