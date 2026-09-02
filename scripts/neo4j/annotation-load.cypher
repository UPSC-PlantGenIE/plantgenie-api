// Annotation nodes from annotations.csv, linked to their Assembly.
//
// Requires assembly-load.cypher to have run first.
//
// id is URL-safe ('betpe-v1.2') and matches the ids the gene loads in
// upsc-plantgenie/neo4j-queries.cypher already expect; path is the directory
// layout. geneCount is the row count of each gene-records CSV, and is set
// again from the graph once the genes themselves are loaded.
//
// Note: the clear step DETACH DELETEs, so it removes HAS_GENE edges too.
// Re-running this means re-running the gene loads afterwards.

CREATE CONSTRAINT annotation_id IF NOT EXISTS FOR (n:Annotation) REQUIRE n.id IS UNIQUE;

// Clear existing annotations (safe to re-run)
MATCH (n:Annotation)
CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///annotations.csv' AS row
MATCH (a:Assembly {id: row.assembly})
CREATE (a)-[:HAS_ANNOTATION]->(:Annotation {
  id:        row.id,
  path:      row.path,
  version:   row.version,
  geneCount: toInteger(row.geneCount),
  isDefault: toBoolean(row.isDefault)
});

// Verification - expect 5 annotations, each reachable from its taxon
MATCH (t:Taxon)-[:HAS_ASSEMBLY]->(a:Assembly)-[:HAS_ANNOTATION]->(n:Annotation)
RETURN t.abbreviation AS taxon, a.id AS assembly, n.id AS id,
       n.version AS version, n.geneCount AS geneCount, n.isDefault AS isDefault
ORDER BY id;
