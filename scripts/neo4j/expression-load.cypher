// Expression data for one experiment: picab-v2.0-cold-roots.
//
// Requires annotation-load.cypher and gene-load.cypher to have run first.
// Needs experiments.csv, picab-cold-roots-samples.csv and
// picab-cold-roots-expression.csv in /opt/neo4j/import.
//
// Gene matches seek on the gene_id index, then check HAS_GENE in a WHERE.
// Matching through (a)-[:HAS_GENE]->(g:Gene {id: ...}) skips the index.
//
// Before the expression load, EXPLAIN it and confirm both
// NodeIndexSeek on Gene(id) and NodeUniqueIndexSeek on Sample(id). A
// NodeByLabelScan on Sample means the sample_id constraint is missing.

CREATE CONSTRAINT experiment_id IF NOT EXISTS FOR (n:Experiment) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sample_id IF NOT EXISTS FOR (n:Sample) REQUIRE n.id IS UNIQUE;

// Clear this experiment only (safe to re-run). Genes are never touched.
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-cold-roots'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-cold-roots'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-cold-roots'})
DETACH DELETE e;

// Experiment, from its row in experiments.csv
LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/cold-roots'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-cold-roots',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

// Samples
MATCH (e:Experiment {id: 'picab-v2.0-cold-roots'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-cold-roots-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

// Expression values. LOAD CSV stays outside the subquery so that
// IN TRANSACTIONS batches the CSV rows. With it inside, the only outer
// row is the annotation, so every write lands in one transaction and
// exhausts the transaction memory pool.
LOAD CSV WITH HEADERS FROM 'file:///picab-cold-roots-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-cold-roots-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// Verification - expect 27 samples and 1,161,621 edges
MATCH (e:Experiment {id: 'picab-v2.0-cold-roots'})<-[:PART_OF]-(s:Sample)
OPTIONAL MATCH (s)<-[r:EXPRESSED_IN]-()
RETURN e.id AS experiment, count(DISTINCT s) AS samples, count(r) AS edges;
