// pinsy (Pinus sylvestris) v1.0 expression: all six experiments.
//
// Requires annotation-load.cypher and gene-load.cypher to have run first.
// CSVs come from scripts/expression/pinsy-expression.sql and land in
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
// pinco-wood-cutting holds Pinus contorta samples mapped onto the pinsy
// annotation, and its unit is vst rather than tpm. Both come from the row
// already in experiments.csv, so nothing here treats it differently.

CREATE CONSTRAINT experiment_id IF NOT EXISTS FOR (n:Experiment) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sample_id IF NOT EXISTS FOR (n:Sample) REQUIRE n.id IS UNIQUE;

// cold-roots
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-cold-roots'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-cold-roots'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'pinsy-v1.0-cold-roots'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'pinsy/v1/v1.0/cold-roots'
MATCH (a:Annotation {id: 'pinsy-v1.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'pinsy-v1.0-cold-roots',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'pinsy-v1.0-cold-roots'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-cold-roots-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///pinsy-cold-roots-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'pinsy-v1.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'pinsy-v1.0-cold-roots-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// cold-needles
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-cold-needles'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-cold-needles'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'pinsy-v1.0-cold-needles'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'pinsy/v1/v1.0/cold-needles'
MATCH (a:Annotation {id: 'pinsy-v1.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'pinsy-v1.0-cold-needles',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'pinsy-v1.0-cold-needles'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-cold-needles-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///pinsy-cold-needles-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'pinsy-v1.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'pinsy-v1.0-cold-needles-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// drought-roots
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-drought-roots'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-drought-roots'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'pinsy-v1.0-drought-roots'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'pinsy/v1/v1.0/drought-roots'
MATCH (a:Annotation {id: 'pinsy-v1.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'pinsy-v1.0-drought-roots',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'pinsy-v1.0-drought-roots'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-drought-roots-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///pinsy-drought-roots-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'pinsy-v1.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'pinsy-v1.0-drought-roots-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// drought-needles
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-drought-needles'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-drought-needles'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'pinsy-v1.0-drought-needles'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'pinsy/v1/v1.0/drought-needles'
MATCH (a:Annotation {id: 'pinsy-v1.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'pinsy-v1.0-drought-needles',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'pinsy-v1.0-drought-needles'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-drought-needles-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///pinsy-drought-needles-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'pinsy-v1.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'pinsy-v1.0-drought-needles-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// wood-cutting
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-wood-cutting'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-wood-cutting'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'pinsy-v1.0-wood-cutting'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'pinsy/v1/v1.0/wood-cutting'
MATCH (a:Annotation {id: 'pinsy-v1.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'pinsy-v1.0-wood-cutting',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'pinsy-v1.0-wood-cutting'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-wood-cutting-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///pinsy-wood-cutting-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'pinsy-v1.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'pinsy-v1.0-wood-cutting-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// pinco-wood-cutting
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-pinco-wood-cutting'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'pinsy-v1.0-pinco-wood-cutting'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'pinsy-v1.0-pinco-wood-cutting'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'pinsy/v1/v1.0/pinco-wood-cutting'
MATCH (a:Annotation {id: 'pinsy-v1.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'pinsy-v1.0-pinco-wood-cutting',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'pinsy-v1.0-pinco-wood-cutting'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///pinsy-pinco-wood-cutting-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///pinsy-pinco-wood-cutting-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'pinsy-v1.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'pinsy-v1.0-pinco-wood-cutting-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;
