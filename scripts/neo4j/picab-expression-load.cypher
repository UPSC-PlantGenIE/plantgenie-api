// picab (Picea abies) v2.0 expression: all nine experiments.
//
// Requires annotation-load.cypher and gene-load.cypher to have run first.
// CSVs come from scripts/expression/picab-expression.sql and land in
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

CREATE CONSTRAINT experiment_id IF NOT EXISTS FOR (n:Experiment) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sample_id IF NOT EXISTS FOR (n:Sample) REQUIRE n.id IS UNIQUE;

// cold-roots
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-cold-roots'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-cold-roots'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-cold-roots'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/cold-roots'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-cold-roots',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

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

LOAD CSV WITH HEADERS FROM 'file:///picab-cold-roots-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-cold-roots-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// cold-needles
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-cold-needles'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-cold-needles'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-cold-needles'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/cold-needles'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-cold-needles',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-cold-needles'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-cold-needles-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-cold-needles-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-cold-needles-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// drought-roots
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-drought-roots'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-drought-roots'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-drought-roots'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/drought-roots'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-drought-roots',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-drought-roots'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-drought-roots-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-drought-roots-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-drought-roots-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// drought-needles
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-drought-needles'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-drought-needles'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-drought-needles'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/drought-needles'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-drought-needles',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-drought-needles'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-drought-needles-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-drought-needles-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-drought-needles-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// somatic-embryogenesis
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-somatic-embryogenesis'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-somatic-embryogenesis'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-somatic-embryogenesis'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/somatic-embryogenesis'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-somatic-embryogenesis',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-somatic-embryogenesis'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-somatic-embryogenesis-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-somatic-embryogenesis-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-somatic-embryogenesis-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// zygotic-embryogenesis
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-zygotic-embryogenesis'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-zygotic-embryogenesis'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-zygotic-embryogenesis'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/zygotic-embryogenesis'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-zygotic-embryogenesis',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-zygotic-embryogenesis'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-zygotic-embryogenesis-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-zygotic-embryogenesis-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-zygotic-embryogenesis-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// exatlas
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-exatlas'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-exatlas'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-exatlas'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/exatlas'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-exatlas',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-exatlas'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-exatlas-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-exatlas-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-exatlas-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// wood-cutting
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-wood-cutting'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-wood-cutting'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-wood-cutting'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/wood-cutting'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-wood-cutting',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-wood-cutting'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-wood-cutting-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-wood-cutting-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-wood-cutting-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// light-variation
MATCH (:Gene)-[r:EXPRESSED_IN]->(:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-light-variation'})
CALL (r) { DELETE r } IN TRANSACTIONS OF 10000 ROWS;

MATCH (s:Sample)-[:PART_OF]->(:Experiment {id: 'picab-v2.0-light-variation'})
DETACH DELETE s;

MATCH (e:Experiment {id: 'picab-v2.0-light-variation'})
DETACH DELETE e;

LOAD CSV WITH HEADERS FROM 'file:///experiments.csv' AS row
WITH row WHERE row.id = 'picab/v2/v2.0/light-variation'
MATCH (a:Annotation {id: 'picab-v2.0'})
CREATE (a)-[:HAS_EXPERIMENT]->(:Experiment {
  id:          'picab-v2.0-light-variation',
  name:        row.name,
  description: row.description,
  unit:        row.unit
});

MATCH (e:Experiment {id: 'picab-v2.0-light-variation'})
CALL (e) {
  LOAD CSV WITH HEADERS FROM 'file:///picab-light-variation-samples.csv' AS row
  FIELDTERMINATOR '\t'
  CREATE (:Sample {
    id:           e.id + '-' + row.abbreviation,
    abbreviation: row.abbreviation,
    group:        toInteger(row.sample_group),
    order:        toInteger(row.sample_number),
    description:  row.description
  })-[:PART_OF]->(e)
};

LOAD CSV WITH HEADERS FROM 'file:///picab-light-variation-expression.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (a:Annotation {id: 'picab-v2.0'})
  MATCH (g:Gene {id: row.gene_id})
  WHERE (a)-[:HAS_GENE]->(g)
  MATCH (s:Sample {id: 'picab-v2.0-light-variation-' + row.sample_id})
  CREATE (g)-[:EXPRESSED_IN {value: toFloat(row.expression_value)}]->(s)
} IN TRANSACTIONS OF 10000 ROWS;

// Verification - expect nine experiments, 330 samples, 14,196,911 edges
MATCH (:Annotation {id: 'picab-v2.0'})-[:HAS_EXPERIMENT]->(e:Experiment)
OPTIONAL MATCH (e)<-[:PART_OF]-(s:Sample)
OPTIONAL MATCH (s)<-[r:EXPRESSED_IN]-()
RETURN e.id AS experiment, e.unit AS unit,
       count(DISTINCT s) AS samples, count(r) AS edges
ORDER BY experiment;
