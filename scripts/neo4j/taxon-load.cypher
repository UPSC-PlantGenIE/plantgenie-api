// Taxon nodes from database-imports/taxa.csv.
//
// Source is hand-maintained and comma-delimited; the DuckDB-generated files
// are tab-delimited.
//
// Note: the clear step DETACH DELETEs, so it removes HAS_ASSEMBLY edges too.
// Re-running this means re-running the assembly load afterwards.

CREATE CONSTRAINT taxon_id IF NOT EXISTS FOR (t:Taxon) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT taxon_abbreviation IF NOT EXISTS FOR (t:Taxon) REQUIRE t.abbreviation IS UNIQUE;

// Clear existing taxa (safe to re-run)
MATCH (t:Taxon)
CALL (t) { DETACH DELETE t } IN TRANSACTIONS OF 1000 ROWS;

LOAD CSV WITH HEADERS FROM 'file:///taxa.csv' AS row
CREATE (:Taxon {
  id:             toInteger(row.taxonId),
  scientificName: row.scientificName,
  abbreviation:   row.abbreviation,
  alias:          CASE WHEN row.alias      = '' THEN null ELSE row.alias      END,
  commonName:     CASE WHEN row.commonName = '' THEN null ELSE row.commonName END
});

// Verification - expect 7 taxa, id as an integer not a string
MATCH (t:Taxon)
RETURN t.id AS id, t.abbreviation AS abbreviation, t.scientificName AS scientificName
ORDER BY id;
