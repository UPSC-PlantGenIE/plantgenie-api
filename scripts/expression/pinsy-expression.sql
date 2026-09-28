-- pinsy (Pinus sylvestris) v1.0 RNA-seq: samples and per-gene expression for
-- all six experiments.
--
--   duckdb -f scripts/expression/pinsy-expression.sql
--
-- Same shape as picab-expression.sql. pinsy lives under v1/v1.0, not v2/v2.0.
-- pinco-wood-cutting is Pinus contorta mapped onto the pinsy annotation and
-- its values are vst, not tpm, which experiments.csv already records.
--
-- Sample ids in every data.parquet were checked against the abbreviation
-- column of the matching metadata.txt before this ran: all six agree exactly.
--
-- data.parquet is wide - one row per transcript, one column per sample - and
-- its feature_id is transcript level (PS_chr01_G000079.mRNA.4). Values are
-- summed across a gene's isoforms, and genes absent from pinsy-gene-records.csv
-- are dropped. Only wood-cutting actually carries several isoforms per gene;
-- the cold and drought parquets are already one row per gene.
--
-- metadata.txt is tab separated with a DuckDB console footer appended, which
-- comment = '#' skips. Its columns are ordered id, group, abbreviation, where
-- picab's are id, abbreviation, group, so the SELECT names them explicitly.
--
-- CSVs land in /opt/neo4j/import, where the load scripts read them.

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/cold-roots/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pinsy-cold-roots-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/cold-roots/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pinsy-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pinsy-cold-roots-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/cold-needles/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pinsy-cold-needles-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/cold-needles/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pinsy-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pinsy-cold-needles-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/drought-roots/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pinsy-drought-roots-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/drought-roots/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pinsy-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pinsy-drought-roots-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/drought-needles/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pinsy-drought-needles-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/drought-needles/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pinsy-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pinsy-drought-needles-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/wood-cutting/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pinsy-wood-cutting-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/wood-cutting/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pinsy-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pinsy-wood-cutting-expression.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/pinco-wood-cutting/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pinsy-pinco-wood-cutting-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.mRNA\.[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pinsy/v1/v1.0/rnaseq/pinco-wood-cutting/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pinsy-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pinsy-pinco-wood-cutting-expression.csv' (HEADER, DELIMITER '\t');
