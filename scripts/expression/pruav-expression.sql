-- pruav (Prunus avium) v2.0 RNA-seq: samples and per-gene expression for its
-- one experiment.
--
--   duckdb -f scripts/expression/pruav-expression.sql
--
-- Same shape as pinsy-expression.sql. pruav's feature_id uses a -T1 transcript
-- suffix (FUN_000003-T1), not picab's .mRNA.1, so the regex differs. Values
-- are summed across a gene's isoforms, and genes absent from
-- pruav-gene-records.csv are dropped.
--
-- 40,097 features reduce to 38,075 genes, every one of which is present in
-- pruav-gene-records.csv, so the gene filter drops nothing here.
--
-- Sample ids in data.parquet were checked against the abbreviation column of
-- metadata.txt before this ran: 82 each way, agreeing exactly.
--
-- metadata.txt is tab separated with a DuckDB console footer appended, which
-- comment = '#' skips.
--
-- CSVs land in /opt/neo4j/import, where the load scripts read them.

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/pruav/v2/v2.0/rnaseq/wood-cutting/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/pruav-wood-cutting-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)-T[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/pruav/v2/v2.0/rnaseq/wood-cutting/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/pruav-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/pruav-wood-cutting-expression.csv' (HEADER, DELIMITER '\t');
