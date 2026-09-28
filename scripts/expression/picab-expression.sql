-- picab (Picea abies) v2.0 RNA-seq: samples and per-gene expression for all
-- nine experiments.
--
--   duckdb -f scripts/expression/picab-expression.sql
--
-- Derived from upsc-plantgenie/duckdb/picab-cold-roots-expression.sql, which
-- produced the cold-roots CSVs already loaded into neo4j.
--
-- data.parquet is wide - one row per transcript, one column per sample - and
-- its feature_id is transcript level (PA_chr01_G000029.mRNA.1). Values are
-- summed across a gene's isoforms, and genes absent from picab-gene-records.csv
-- are dropped: expression covers rRNA, tRNA and TE features that are
-- deliberately not Gene nodes.
--
-- metadata.txt is tab separated with a DuckDB console footer appended, which
-- comment = '#' skips. The somatic-embryogenesis header carried a trailing
-- space on its first column until 2026-09-24, when it was stripped so that
-- every experiment reads the same way.
--
-- CSVs land in /opt/neo4j/import, where the load scripts read them.

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/cold-roots/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-cold-roots-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/cold-roots/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-cold-roots-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/cold-needles/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-cold-needles-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/cold-needles/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-cold-needles-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/drought-roots/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-drought-roots-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/drought-roots/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-drought-roots-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/drought-needles/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-drought-needles-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/drought-needles/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-drought-needles-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/somatic-embryogenesis/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-somatic-embryogenesis-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/somatic-embryogenesis/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-somatic-embryogenesis-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/zygotic-embryogenesis/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-zygotic-embryogenesis-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/zygotic-embryogenesis/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-zygotic-embryogenesis-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/exatlas/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-exatlas-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/exatlas/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-exatlas-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/wood-cutting/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-wood-cutting-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/wood-cutting/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-wood-cutting-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/light-variation/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/picab-light-variation-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/picab/v2/v2.0/rnaseq/light-variation/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/picab-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/picab-light-variation-expression.csv' (HEADER, DELIMITER '\t');

SELECT 'cold-roots' AS stub,
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-cold-roots-samples.csv', delim='\t', header=true)) AS samples,
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-cold-roots-expression.csv', delim='\t', header=true)) AS expression_rows
UNION ALL SELECT 'cold-needles',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-cold-needles-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-cold-needles-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'drought-roots',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-drought-roots-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-drought-roots-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'drought-needles',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-drought-needles-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-drought-needles-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'somatic-embryogenesis',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-somatic-embryogenesis-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-somatic-embryogenesis-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'zygotic-embryogenesis',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-zygotic-embryogenesis-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-zygotic-embryogenesis-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'exatlas',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-exatlas-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-exatlas-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'wood-cutting',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-wood-cutting-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-wood-cutting-expression.csv', delim='\t', header=true))
UNION ALL SELECT 'light-variation',
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-light-variation-samples.csv', delim='\t', header=true)),
       (SELECT count(*) FROM read_csv('/opt/neo4j/import/picab-light-variation-expression.csv', delim='\t', header=true));
