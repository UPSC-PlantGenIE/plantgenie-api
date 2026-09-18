-- Gene to GO term pairs for the T89 phased Populus tremula assembly.
--
-- The eggnog GOs column holds a comma-separated list per transcript, so
-- is_longest = 1 picks the representative transcript per gene and the list
-- is exploded into one row per pair.
--
-- Split the same way as the gene records: T89h1, T89h2, and the organelles,
-- which are shared by both haplotypes and so are loaded once.

CREATE OR REPLACE TEMP VIEW t89_gene_go AS
with exploded as (
  select
    gene_id,
    unnest(string_split(GOs, ',')) as go_id
  from read_csv(
    '/opt/data/plantgenie-knowledge/potra/T89-2026/T89.eggnog.transcript.tsv',
    delim = '\t',
    header = true,
    nullstr = '-'
  )
  where is_longest = 1 and GOs is not null
)
select distinct gene_id, trim(go_id) as go_id
from exploded
where trim(go_id) <> '';

COPY (select * from t89_gene_go where gene_id like 'T89h1%')
  TO '/opt/neo4j/import/potra-T89-2026-h1-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (select * from t89_gene_go where gene_id like 'T89h2%')
  TO '/opt/neo4j/import/potra-T89-2026-h2-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (select * from t89_gene_go where gene_id like 'T89pt%' or gene_id like 'T89mt%')
  TO '/opt/neo4j/import/potra-T89-2026-organelle-gene-go.csv' (HEADER, DELIMITER '\t');
