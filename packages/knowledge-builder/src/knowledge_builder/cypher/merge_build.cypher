UNWIND $asset_rows AS row
MERGE (a:Asset {id: row.id})
SET a.name = row.name,
    a.format = row.format,
    a.object = row.object,
    a.bucketUri = row.bucketUri,
    a.sourceUrl = row.sourceUrl
;

UNWIND $annotation_from_rows AS row
MATCH (a:Asset {id: row.assetId})
MATCH (ann:Annotation {id: row.annotationId})
MERGE (a)-[:FROM]->(ann)
;

UNWIND $assembly_from_rows AS row
MATCH (a:Asset {id: row.assetId})
MATCH (asm:Assembly {id: row.assemblyId})
MERGE (a)-[:FROM]->(asm)
;

UNWIND $build_step_rows AS row
MERGE (s:BuildStep {id: row.id})
;

UNWIND $load_step_rows AS row
MERGE (s:LoadStep {id: row.id})
;

UNWIND $build_read_rows AS row
MATCH (a:Asset {id: row.assetId})
MATCH (s:BuildStep {id: row.stepId})
MERGE (a)-[:READ_BY]->(s)
;

UNWIND $build_write_rows AS row
MATCH (s:BuildStep {id: row.stepId})
MATCH (a:Asset {id: row.assetId})
MERGE (s)-[:WRITES]->(a)
;

UNWIND $load_read_rows AS row
MATCH (a:Asset {id: row.assetId})
MATCH (s:LoadStep {id: row.stepId})
MERGE (a)-[:READ_BY]->(s)
;

UNWIND $requires_rows AS row
MATCH (from:LoadStep {id: row.fromId})
MATCH (to:LoadStep {id: row.toId})
MERGE (from)-[:REQUIRES]->(to)
;
