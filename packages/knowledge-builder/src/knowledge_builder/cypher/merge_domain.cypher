UNWIND $taxon_rows AS row
MERGE (n:Taxon {id: row.id})
SET n.abbreviation = row.abbreviation,
    n.scientificName = row.scientificName,
    n.alias = row.alias,
    n.commonName = row.commonName
;

UNWIND $assembly_rows AS row
MATCH (t:Taxon {id: row.taxonId})
MERGE (a:Assembly {id: row.id})
SET a.version = row.version,
    a.versionName = row.versionName,
    a.published = row.published,
    a.publicationDate = row.publicationDate,
    a.doi = row.doi
MERGE (a)-[:OF]->(t)
;

UNWIND $annotation_rows AS row
MATCH (a:Assembly {id: row.assemblyId})
MERGE (n:Annotation {id: row.id})
SET n.slug = row.slug,
    n.geneCount = row.geneCount,
    n.isDefault = row.isDefault
MERGE (n)-[:OF]->(a)
;
