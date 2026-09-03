// Gene nodes per annotation, linked with HAS_GENE.
//
// Requires annotation-load.cypher to have run first.
//
CREATE INDEX gene_id IF NOT EXISTS FOR (g:Gene) ON (g.id);

// arath-araport11
MATCH (:Annotation {id: 'arath-araport11'})-[:HAS_GENE]->(g:Gene)
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'arath-araport11'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///arath-araport11-gene-records.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (g:Gene {
    id: row.gene_id,
    name: row.gene_name,
    description: row.description,
    chromosome: row.chromosome,
    startPosition: toInteger(row.start_position),
    endPosition: toInteger(row.end_position),
    strand: row.strand
  })
  CREATE (a)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// betpe-v1.2
MATCH (:Annotation {id: 'betpe-v1.2'})-[:HAS_GENE]->(g:Gene)
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'betpe-v1.2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///betpe-gene-records.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (g:Gene {
    id: row.gene_id,
    name: row.gene_name,
    description: row.description,
    chromosome: row.chromosome,
    startPosition: toInteger(row.start_position),
    endPosition: toInteger(row.end_position),
    strand: row.strand
  })
  CREATE (a)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// picab-v2.0
MATCH (:Annotation {id: 'picab-v2.0'})-[:HAS_GENE]->(g:Gene)
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'picab-v2.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-gene-records.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (g:Gene {
    id: row.gene_id,
    name: row.gene_name,
    description: row.description,
    chromosome: row.chromosome,
    startPosition: toInteger(row.start_position),
    endPosition: toInteger(row.end_position),
    strand: row.strand
  })
  CREATE (a)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// pinsy-v1.0
MATCH (:Annotation {id: 'pinsy-v1.0'})-[:HAS_GENE]->(g:Gene)
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'pinsy-v1.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-gene-records.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (g:Gene {
    id: row.gene_id,
    name: row.gene_name,
    description: row.description,
    chromosome: row.chromosome,
    startPosition: toInteger(row.start_position),
    endPosition: toInteger(row.end_position),
    strand: row.strand
  })
  CREATE (a)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// potra-v2.2
MATCH (:Annotation {id: 'potra-v2.2'})-[:HAS_GENE]->(g:Gene)
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'potra-v2.2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-gene-records.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (g:Gene {
    id: row.gene_id,
    name: row.gene_name,
    description: row.description,
    chromosome: row.chromosome,
    startPosition: toInteger(row.start_position),
    endPosition: toInteger(row.end_position),
    strand: row.strand
  })
  CREATE (a)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// pruav-v2.0
MATCH (:Annotation {id: 'pruav-v2.0'})-[:HAS_GENE]->(g:Gene)
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'pruav-v2.0'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///pruav-gene-records.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (g:Gene {
    id: row.gene_id,
    name: row.gene_name,
    description: row.description,
    chromosome: row.chromosome,
    startPosition: toInteger(row.start_position),
    endPosition: toInteger(row.end_position),
    strand: row.strand
  })
  CREATE (a)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification - expect 27655, 28147, 43382, 49387, 37184, 39984
MATCH (a:Annotation)-[:HAS_GENE]->(g:Gene)
RETURN a.id AS annotation, count(g) AS geneCount
ORDER BY annotation;
