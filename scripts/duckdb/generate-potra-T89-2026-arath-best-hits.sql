-- Best Araport11 diamond hit per gene for the T89 haplotypes.
--
-- Input is the unfiltered diamond blastx output (translated CDS against
-- Araport11 proteins), which keeps up to 25 subjects per query, so the top
-- row per gene is picked here by evalue, then bitscore.
--
-- Both query and subject carry a transcript suffix to strip. The organelle
-- genes are in both haplotype runs, so they are taken from h1 alone and
-- loaded once as shared nodes.

CREATE OR REPLACE TEMP MACRO best_hits(source) AS TABLE
  with hits as (
    select
      regexp_extract(qseqid, '^(.+)\.\d+$', 1) as gene_id,
      regexp_extract(sseqid, '^(.+)\.\d+$', 1) as arath_gene_id,
      evalue,
      bitscore
    from read_csv(
      source,
      delim = '\t',
      header = false,
      columns = {
        'qseqid': 'VARCHAR', 'sseqid': 'VARCHAR', 'pident': 'DOUBLE',
        'length': 'BIGINT', 'mismatch': 'BIGINT', 'gapopen': 'BIGINT',
        'qstart': 'BIGINT', 'qend': 'BIGINT', 'sstart': 'BIGINT',
        'send': 'BIGINT', 'evalue': 'DOUBLE', 'bitscore': 'DOUBLE'
      }
    )
  )
  select gene_id, arath_gene_id, evalue, bitscore
  from hits
  qualify row_number() over (
    partition by gene_id
    order by evalue asc, bitscore desc
  ) = 1;

COPY (
  select * from best_hits('/opt/data/plantgenie-knowledge/potra/T89-2026/h1/diamond/arath-best-diamond-hits.tsv.gz')
  where gene_id like 'T89h1%'
) TO '/opt/neo4j/import/potra-T89-2026-h1-arath-best-hits.csv' (HEADER, DELIMITER '\t');

COPY (
  select * from best_hits('/opt/data/plantgenie-knowledge/potra/T89-2026/h2/diamond/arath-best-diamond-hits.tsv.gz')
  where gene_id like 'T89h2%'
) TO '/opt/neo4j/import/potra-T89-2026-h2-arath-best-hits.csv' (HEADER, DELIMITER '\t');

COPY (
  select * from best_hits('/opt/data/plantgenie-knowledge/potra/T89-2026/h1/diamond/arath-best-diamond-hits.tsv.gz')
  where gene_id like 'T89pt%' or gene_id like 'T89mt%'
) TO '/opt/neo4j/import/potra-T89-2026-organelle-arath-best-hits.csv' (HEADER, DELIMITER '\t');
