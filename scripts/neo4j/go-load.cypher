// GO graph: terms, IS_A / PART_OF edges, alt-id aliases.
//
// Independent of the taxon/assembly/annotation seed. Nothing depends on this
// until the gene-to-GO load.

CREATE CONSTRAINT go_term_id  IF NOT EXISTS FOR (t:GoTerm)  REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT go_alias_id IF NOT EXISTS FOR (a:GoAlias) REQUIRE a.id IS UNIQUE;

// Clear existing GO graph (safe to re-run)
MATCH (t:GoTerm)
CALL (t) { DETACH DELETE t } IN TRANSACTIONS OF 5000 ROWS;

MATCH (a:GoAlias)
CALL (a) { DETACH DELETE a } IN TRANSACTIONS OF 5000 ROWS;

// GoTerm nodes
LOAD CSV WITH HEADERS FROM 'file:///go-terms.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  CREATE (:GoTerm {
    id: row.id,
    name: row.name,
    namespace:  CASE WHEN row.namespace  = '' THEN null ELSE row.namespace  END,
    definition: CASE WHEN row.definition = '' THEN null ELSE row.definition END,
    isObsolete: toBoolean(row.is_obsolete)
  })
} IN TRANSACTIONS OF 1000 ROWS;

// IS_A / PART_OF edges
LOAD CSV WITH HEADERS FROM 'file:///go-edges.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (from:GoTerm {id: row.from_id})
  MATCH (to:GoTerm   {id: row.to_id})
  CREATE (from)-[:$(row.type)]->(to)
} IN TRANSACTIONS OF 1000 ROWS;

// GoAlias nodes + IS_ALIAS_OF edges
LOAD CSV WITH HEADERS FROM 'file:///go-aliases.csv' AS row
FIELDTERMINATOR '\t'
CALL (row) {
  MATCH (canonical:GoTerm {id: row.canonical_id})
  CREATE (alias:GoAlias {id: row.alt_id})
  CREATE (alias)-[:IS_ALIAS_OF]->(canonical)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification
          MATCH (t:GoTerm)             RETURN 'goTermCount'    AS metric, count(t) AS value
UNION ALL MATCH (a:GoAlias)            RETURN 'goAliasCount'   AS metric, count(a) AS value
UNION ALL MATCH ()-[r:IS_A]->()        RETURN 'isACount'       AS metric, count(r) AS value
UNION ALL MATCH ()-[r:PART_OF]->()     RETURN 'partOfCount'    AS metric, count(r) AS value
UNION ALL MATCH ()-[r:IS_ALIAS_OF]->() RETURN 'isAliasOfCount' AS metric, count(r) AS value;
