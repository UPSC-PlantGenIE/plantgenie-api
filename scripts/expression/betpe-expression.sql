-- betpe (Betula pendula) v1.4 RNA-seq: samples and per-gene expression for its
-- one experiment.
--
--   duckdb -f scripts/expression/betpe-expression.sql
--
-- Same shape as pruav-expression.sql, with one difference that matters.
--
-- betpe's data.parquet mixes two transcript conventions. 25,865 features end
-- .mRNA1 and 226 end .m0002, and both forms carry real gene ids - the .mNNNN
-- form alone accounts for 220 genes present in the annotation. A regex for
-- either one on its own silently drops or undercounts them, so the pattern
-- here accepts both. The parquet also carries 1,455 features named after a
-- protein description (50S_ribosomal_protein_L11.mRNA1) and 2 Arabidopsis ids;
-- none are in the annotation, so the gene filter removes them.
--
-- The values were quantified against the v1.2 transcriptome and are carried
-- over unchanged: gene ids are shared between the two annotations, but 3,390
-- v1.2 transcripts are absent from v1.4 and the vst fit was made over the v1.2
-- gene set. 22,543 of v1.4's 24,861 genes get values.
--
-- Sample ids in data.parquet were checked against the abbreviation column of
-- metadata.txt before this ran: 66 each way, agreeing exactly.
--
-- CSVs land in /opt/neo4j/import, where the load scripts read them.

COPY (
  SELECT id AS sample_number, abbreviation, "group" AS sample_group,
         description, reference
  FROM read_csv('/opt/data/plantgenie-knowledge/betpe/v1/v1.4/rnaseq/wood-cutting/metadata.txt',
                delim = '\t', header = true, comment = '#')
  ORDER BY sample_number
) TO '/opt/neo4j/import/betpe-wood-cutting-samples.csv' (HEADER, DELIMITER '\t');

COPY (
  with long as (
    unpivot (
      select regexp_extract(feature_id, '^(.*)\.m(?:RNA)?[0-9]+$', 1) as gene_id,
             * exclude (feature_id)
      from read_parquet('/opt/data/plantgenie-knowledge/betpe/v1/v1.4/rnaseq/wood-cutting/data.parquet')
    )
    on columns(* exclude (gene_id))
    into name sample_id value expression_value
  ),
  genes as (
    select gene_id from read_csv('/opt/neo4j/import/betpe-v1.4-gene-records.csv',
                                 delim = '\t', header = true)
  )
  select gene_id, sample_id, sum(expression_value) as expression_value
  from long
  where gene_id in (select gene_id from genes)
  group by gene_id, sample_id
) TO '/opt/neo4j/import/betpe-wood-cutting-expression.csv' (HEADER, DELIMITER '\t');
