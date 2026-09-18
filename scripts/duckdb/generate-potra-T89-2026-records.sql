-- Gene records for the T89 phased Populus tremula assembly.
--
-- One assembly (potra-T89-2026) carrying both haplotypes, split into two
-- annotations on the gene id prefix: T89h1 and T89h2. The plastid and
-- mitochondrial genes belong to neither haplotype, so they go to a third
-- file and are loaded once as shared nodes with an edge to each annotation.
--
-- Coordinates come from the gff3 gene features; names and descriptions come
-- from the eggnog table, where is_longest = 1 selects exactly one transcript
-- per gene.

CREATE OR REPLACE TEMP VIEW t89_genes AS
with
  gff as (
    select
      regexp_extract(attributes, 'ID=([^;]+)', 1) as gene_id,
      seqid, start, "end", strand
    from read_csv(
      '/opt/data/plantgenie-knowledge/potra/T89-2026/T89.annotation.gff3',
      header = false,
      delim = '\t',
      comment = '#',
      columns = {
        'seqid': 'VARCHAR', 'source': 'VARCHAR', 'feature_type': 'VARCHAR',
        'start': 'BIGINT', 'end': 'BIGINT', 'score': 'VARCHAR',
        'strand': 'VARCHAR', 'phase': 'VARCHAR', 'attributes': 'VARCHAR'
      },
      auto_detect = false,
      nullstr = '.'
    )
    where lower(feature_type) = 'gene'
  ),
  eggnog as (
    select gene_id, Preferred_name as gene_name, Description as description
    from read_csv(
      '/opt/data/plantgenie-knowledge/potra/T89-2026/T89.eggnog.transcript.tsv',
      delim = '\t',
      header = true,
      nullstr = '-'
    )
    where is_longest = 1
  )
select
  gff.gene_id,
  eggnog.gene_name,
  eggnog.description,
  gff.seqid as chromosome,
  gff.start as start_position,
  gff."end" as end_position,
  gff.strand
from gff
  left join eggnog on eggnog.gene_id = gff.gene_id;

COPY (select * from t89_genes where gene_id like 'T89h1%')
  TO '/opt/neo4j/import/potra-T89-2026-h1-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (select * from t89_genes where gene_id like 'T89h2%')
  TO '/opt/neo4j/import/potra-T89-2026-h2-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (select * from t89_genes where chromosome in ('pt', 'mt'))
  TO '/opt/neo4j/import/potra-T89-2026-organelle-gene-records.csv' (HEADER, DELIMITER '\t');
