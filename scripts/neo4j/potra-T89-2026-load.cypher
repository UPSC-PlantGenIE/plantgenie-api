// The T89 phased Populus tremula assembly: one Assembly carrying both
// haplotypes, split into two Annotations on the gene id prefix.
//
// Requires taxon-load.cypher to have run first. Gene records come from
// scripts/duckdb/generate-potra-T89-2026-records.sql.
//
// The plastid and mitochondrial genes belong to neither haplotype, so they
// are loaded once and given an edge to each annotation. The haplotype clear
// steps exclude them, so re-running one haplotype leaves the other intact.

// Assembly
LOAD CSV WITH HEADERS FROM 'file:///assemblies.csv' AS row
WITH row WHERE row.id = 'potra-T89-2026'
MATCH (t:Taxon {abbreviation: row.taxon})
MERGE (t)-[:HAS_ASSEMBLY]->(a:Assembly {id: row.id})
SET a.path      = row.path,
    a.version   = row.version,
    a.published = toBoolean(row.published);

// Annotations
LOAD CSV WITH HEADERS FROM 'file:///annotations.csv' AS row
WITH row WHERE row.assembly = 'potra-T89-2026'
MATCH (a:Assembly {id: row.assembly})
MERGE (a)-[:HAS_ANNOTATION]->(n:Annotation {id: row.id})
SET n.path      = row.path,
    n.version   = row.version,
    n.geneCount = toInteger(row.geneCount),
    n.isDefault = toBoolean(row.isDefault);

// potra-T89-2026-h1
MATCH (:Annotation {id: 'potra-T89-2026-h1'})-[:HAS_GENE]->(g:Gene)
WHERE NOT g.chromosome IN ['pt', 'mt']
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h1'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-h1-gene-records.csv' AS row
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

// potra-T89-2026-h2
MATCH (:Annotation {id: 'potra-T89-2026-h2'})-[:HAS_GENE]->(g:Gene)
WHERE NOT g.chromosome IN ['pt', 'mt']
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (a:Annotation {id: 'potra-T89-2026-h2'})
CALL (a) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-h2-gene-records.csv' AS row
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

// Organelles, shared by both haplotypes
MATCH (g:Gene)
WHERE g.id STARTS WITH 'T89pt' OR g.id STARTS WITH 'T89mt'
CALL (g) { DETACH DELETE g } IN TRANSACTIONS OF 1000 ROWS;

MATCH (h1:Annotation {id: 'potra-T89-2026-h1'})
MATCH (h2:Annotation {id: 'potra-T89-2026-h2'})
CALL (h1, h2) {
  LOAD CSV WITH HEADERS FROM 'file:///potra-T89-2026-organelle-gene-records.csv' AS row
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
  CREATE (h1)-[:HAS_GENE]->(g)
  CREATE (h2)-[:HAS_GENE]->(g)
} IN TRANSACTIONS OF 1000 ROWS;

// Verification - expect 34066 and 33987
MATCH (a:Annotation)-[:HAS_GENE]->(g:Gene)
WHERE a.id STARTS WITH 'potra-T89-2026'
RETURN a.id AS annotation, count(g) AS geneCount
ORDER BY annotation;
