// potra (Populus tremula) v2.2 expression: its one experiment.
//
// Requires annotation-load.cypher and gene-load.cypher to have run first.
// CSVs come from scripts/expression/potra-expression.sql and land in
// /opt/neo4j/import.
//
// Gene matches seek on the gene_id index, then check HAS_GENE in a WHERE.
// Matching through (a)-[:HAS_GENE]->(g:Gene {id: ...}) skips the index.
//
// LOAD CSV stays outside the subquery so IN TRANSACTIONS batches the CSV
// rows. With it inside, the only outer row is the annotation, so every write
// lands in one transaction and exhausts the transaction memory pool.
//
// Clearing deletes this experiment's edges and Sample nodes only. Gene nodes
// are shared with every other experiment and are never touched.
//
// This annotation also has the two T89-2026 haplotypes alongside it, which
// have no expression. Every match here is scoped to potra-v2.2.

CREATE CONSTRAINT experiment_id IF NOT EXISTS FOR (n:Experiment) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sample_id IF NOT EXISTS FOR (n:Sample) REQUIRE n.id IS UNIQUE;

// wood-cutting
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'potra-v2.2-wood-cutting'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'potra-v2.2-wood-cutting'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'potra-v2.2-wood-cutting'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'potra/v2/v2.2/wood-cutting'
MATCH (a:Annotation {id: 'potra-v2.2'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'potra-v2.2-wood-cutting',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'potra-v2.2-wood-cutting'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-wood-cutting-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///potra-wood-cutting-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'potra-v2.2'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'potra-v2.2-wood-cutting-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;
