-- Best Araport11 diamond hit per gene, one statement per taxon.
--
-- The diamond output is transcript-to-transcript and keeps several rows per
-- query, so each statement strips its own transcript suffix and keeps the top
-- row per gene by evalue, then bitscore.

COPY (
  with hits as (
    select
      regexp_extract(qseqid, '^(.+)\.m\d+$', 1) as gene_id,
      regexp_extract(sseqid, '^(.+)\.\d+$', 1) as arath_gene_id,
      evalue,
      bitscore
    from
      read_csv(
        '/Users/jamie/Projects/plantgenie/api/Bepen_v1p2_Araport11_best_diamond_hits.tsv.gz',
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
  qualify
    row_number() over (
      partition by gene_id
      order by evalue asc, bitscore desc
    ) = 1
) TO '/opt/neo4j/import/betpe-arath-best-hits.csv' (HEADER, DELIMITER '\t');

COPY (
  with hits as (
    select
      regexp_extract(qseqid, '^(.+)\.mRNA\.\d+$', 1) as gene_id,
      regexp_extract(sseqid, '^(.+)\.\d+$', 1) as arath_gene_id,
      evalue,
      bitscore
    from
      read_csv(
        '/Users/jamie/Projects/plantgenie/api/Picab02_230926_Araport11_best_diamond_hits.tsv.gz',
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
  qualify
    row_number() over (
      partition by gene_id
      order by evalue asc, bitscore desc
    ) = 1
) TO '/opt/neo4j/import/picab-arath-best-hits.csv' (HEADER, DELIMITER '\t');

COPY (
  with hits as (
    select
      regexp_extract(qseqid, '^(.+)\.mRNA\.\d+$', 1) as gene_id,
      regexp_extract(sseqid, '^(.+)\.\d+$', 1) as arath_gene_id,
      evalue,
      bitscore
    from
      read_csv(
        '/Users/jamie/Projects/plantgenie/api/Pinsy01_240308_Araport11_best_diamond_hits.tsv.gz',
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
  qualify
    row_number() over (
      partition by gene_id
      order by evalue asc, bitscore desc
    ) = 1
) TO '/opt/neo4j/import/pinsy-arath-best-hits.csv' (HEADER, DELIMITER '\t');

COPY (
  with hits as (
    select
      regexp_extract(qseqid, '^(.+)\.\d+$', 1) as gene_id,
      regexp_extract(sseqid, '^(.+)\.\d+$', 1) as arath_gene_id,
      evalue,
      bitscore
    from
      read_csv(
        '/Users/jamie/Projects/plantgenie/api/Potra_v2p2_Araport11_best_diamond_hits.tsv.gz',
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
  qualify
    row_number() over (
      partition by gene_id
      order by evalue asc, bitscore desc
    ) = 1
) TO '/opt/neo4j/import/potra-arath-best-hits.csv' (HEADER, DELIMITER '\t');

COPY (
  with hits as (
    select
      regexp_extract(qseqid, '^(.+)-T\d+$', 1) as gene_id,
      regexp_extract(sseqid, '^(.+)\.\d+$', 1) as arath_gene_id,
      evalue,
      bitscore
    from
      read_csv(
        '/Users/jamie/Projects/plantgenie/api/Pruav_v1_Araport11_best_diamond_hits.tsv.gz',
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
  qualify
    row_number() over (
      partition by gene_id
      order by evalue asc, bitscore desc
    ) = 1
) TO '/opt/neo4j/import/pruav-arath-best-hits.csv' (HEADER, DELIMITER '\t');
