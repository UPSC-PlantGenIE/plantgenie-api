// longestTranscriptId on Gene nodes, for the sequence endpoint.
//
// CSV comes from scripts/neo4j/generate-longest-transcripts-csv.py.
// Re-runnable: SET overwrites, so no clear step is needed.
//
// The gene is matched by index seek and the annotation checked with a
// WHERE existence test. Binding the annotation first and expanding
// HAS_GENE instead loses the gene_id index.

LOAD CSV WITH HEADERS FROM 'file:///longest-transcripts.csv' AS row
CALL (row) {
  MATCH (g:Gene {id: row.geneId})
  MATCH (n:Annotation {path: row.path})
  WHERE (n)-[:HAS_GENE]->(g)
  SET g.longestTranscriptId = row.longestTranscriptId
} IN TRANSACTIONS OF 10000 ROWS;

// Verification
MATCH (a:Annotation)-[:HAS_GENE]->(g:Gene)
RETURN a.id AS annotation,
       count(g) AS genes,
       count(g.longestTranscriptId) AS withTranscript
ORDER BY annotation;
