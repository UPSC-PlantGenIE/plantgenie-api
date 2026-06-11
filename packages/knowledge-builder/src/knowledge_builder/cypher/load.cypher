CREATE INDEX gene_id IF NOT EXISTS FOR (n:Gene) ON (n.id)
;

CREATE INDEX go_term_id IF NOT EXISTS FOR (n:GoTerm) ON (n.id)
;

CALL db.awaitIndexes()
;

LOAD CSV WITH HEADERS FROM 'file:///go-terms.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MERGE (t:GoTerm {id: row.id})
  SET t.name = row.name,
      t.namespace = row.namespace,
      t.definition = row.definition,
      t.isObsolete = (row.is_obsolete = 'true')
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///go-edges.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  WITH row WHERE row.type = 'IS_A'
  MATCH (from:GoTerm {id: row.from_id})
  MATCH (to:GoTerm {id: row.to_id})
  MERGE (from)-[:IS_A]->(to)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///go-edges.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  WITH row WHERE row.type = 'PART_OF'
  MATCH (from:GoTerm {id: row.from_id})
  MATCH (to:GoTerm {id: row.to_id})
  MERGE (from)-[:PART_OF]->(to)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///betpe-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'betpe/v1/v1.2'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///betpe-gene-go.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MERGE (g:Gene {id: row.gene_id})
  MERGE (t:GoTerm {id: row.go_id})
  MERGE (g)-[:HAS_GO]->(t)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///picab-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'picab/v2/v2.0'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///picab-gene-go.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MERGE (g:Gene {id: row.gene_id})
  MERGE (t:GoTerm {id: row.go_id})
  MERGE (g)-[:HAS_GO]->(t)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///pinsy-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'pinsy/v1/v1.0'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///pinsy-gene-go.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MERGE (g:Gene {id: row.gene_id})
  MERGE (t:GoTerm {id: row.go_id})
  MERGE (g)-[:HAS_GO]->(t)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///potra-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'potra/v2/v2.2'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///potra-gene-go.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MERGE (g:Gene {id: row.gene_id})
  MERGE (t:GoTerm {id: row.go_id})
  MERGE (g)-[:HAS_GO]->(t)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///pruav-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'pruav/v2/v2.0'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///pruav-gene-go.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MERGE (g:Gene {id: row.gene_id})
  MERGE (t:GoTerm {id: row.go_id})
  MERGE (g)-[:HAS_GO]->(t)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///arath-tair10-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'arath/tair10/tair10'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;

LOAD CSV WITH HEADERS FROM 'file:///arath-araport11-gene-records.csv' AS row FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (ann:Annotation {id: 'arath/tair10/araport11'})
  MERGE (g:Gene {id: row.gene_id})
  SET g.name = row.gene_name,
      g.description = row.description,
      g.chromosome = row.chromosome,
      g.startPosition = toInteger(row.start_position),
      g.endPosition = toInteger(row.end_position),
      g.strand = row.strand
  MERGE (g)-[:OF]->(ann)
} IN TRANSACTIONS OF 5000 ROWS
;
