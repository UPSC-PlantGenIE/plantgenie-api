// Assembly nodes from database-imports/assemblies.csv, linked to their Taxon.
//
// Requires taxon-load.cypher to have run first.
//
// id is URL-safe ('betpe-v1') because it appears in v2 API paths; path is the
// directory layout ('betpe/v1'). Source is hand-maintained and comma-delimited.

CREATE CONSTRAINT assembly_id IF NOT EXISTS FOR (a:Assembly) REQUIRE a.id IS UNIQUE;

// Clear existing assemblies (safe to re-run)
MATCH (a:Assembly)
CALL (a) { DETACH DELETE a } IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///assemblies.csv' AS row
MATCH (t:Taxon {abbreviation: row.taxon})
CREATE (t)-[:HAS_ASSEMBLY]->(:Assembly {
  id:        row.id,
  path:      row.path,
  version:   row.version,
  published: toBoolean(row.published)
});

// Verification - expect 6 assemblies, each with its taxon
MATCH (t:Taxon)-[:HAS_ASSEMBLY]->(a:Assembly)
RETURN t.abbreviation AS taxon, a.id AS id, a.path AS path,
       a.version AS version, a.published AS published
ORDER BY id;
