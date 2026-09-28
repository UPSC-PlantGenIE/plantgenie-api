-- potra (Populus tremula) v2.2 RNA-seq: samples and per-gene expression for
-- its one experiment.
--
--   duckdb -f scripts/expression/potra-expression.sql
--
-- Same shape as pinsy-expression.sql, with one difference: potra's feature_id
-- is already gene level (Potra2n8c18528), with no transcript suffix to strip,
-- so there is nothing to sum across isoforms. The GROUP BY stays so the query
-- reads like the others and still holds if isoforms ever appear.
--
-- All 37,075 features are present in potra-gene-records.csv, so nothing is
-- dropped by the gene filter.
--
-- Sample ids in data.parquet were checked against the abbreviation column of
-- metadata.txt before this ran: 106 each way, agreeing exactly.
--
-- metadata.txt is tab separated with a DuckDB console footer appended, which
-- comment = '#' skips.
--
-- CSVs land in /opt/neo4j/import, where the load scripts read them.

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/potra/v2/v2.2/rnaseq/wood-cutting/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/potra-wood-cutting-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select feature_id as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/potra/v2/v2.2/rnaseq/wood-cutting/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/potra-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/potra-wood-cutting-expression.csv' (HEADER, DELIMITER '\t');
