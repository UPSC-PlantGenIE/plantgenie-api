COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        regexp_extract(attributes, 'Bpev[^,;]*\.m[0-9]+', 0) AS m_alias,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Bepen_v1p2_coge_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source = 'CoGe'
    ),
    gff_mrna as (
      select * from gff_all
      where lower(feature_type) = 'mrna' AND m_alias is not null
    ),
    gff_gene as (
      select * from gff_all where lower(feature_type) = 'gene'
    ),
    eggnog_annotations as (
      select
        query as feature_id,
        Description as description,
        score,
        Preferred_name as gene_name
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Bepen_v1p2_eggnog_annotation.tsv.gz',
          comment = '#',
          nullstr = '-'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.gene_name,
        eggnog_annotations.description
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.m_alias)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select
    gff_gene.feature_id as gene_id,
    gene_best_eggnog.gene_name,
    gene_best_eggnog.description,
    gff_gene.seqid as chromosome,
    gff_gene.start as start_position,
    gff_gene."end" as end_position,
    gff_gene.strand
  from
    gff_gene
    LEFT JOIN gene_best_eggnog ON (gene_best_eggnog.gene_id = gff_gene.feature_id)
) TO '/opt/neo4j/import/betpe-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        regexp_extract(attributes, 'Bpev[^,;]*\.m[0-9]+', 0) AS m_alias,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Bepen_v1p2_coge_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source = 'CoGe'
    ),
    gff_mrna as (
      select * from gff_all
      where lower(feature_type) = 'mrna' AND m_alias is not null
    ),
    eggnog_annotations as (
      select
        query as feature_id,
        score,
        GOs as go_terms
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Bepen_v1p2_eggnog_annotation.tsv.gz',
          comment = '#',
          nullstr = '-'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.go_terms
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.m_alias)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select distinct
    gene_id,
    trim(go_id) as go_id
  from
    gene_best_eggnog,
    unnest(str_split(go_terms, ',')) as t(go_id)
  where
    go_terms is not null
    and trim(go_id) like 'GO:%'
) TO '/opt/neo4j/import/betpe-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Picab02_230926_at01_longest_no_TE_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source in ['PASN', 'manual', 'PASA']
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    gff_gene as (
      select * from gff_all where lower(feature_type) = 'gene'
    ),
    eggnog_annotations as (
      select
        id as feature_id,
        eggnog_description as description,
        eggnog_score as score,
        eggnog_preferred_name as gene_name
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Picab02_230926_at01_longest_representative_annotations_merged_sorted_non_redundant_panthers.tsv.gz',
          nullstr = 'NA'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.gene_name,
        eggnog_annotations.description
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select
    gff_gene.feature_id as gene_id,
    gene_best_eggnog.gene_name,
    gene_best_eggnog.description,
    gff_gene.seqid as chromosome,
    gff_gene.start as start_position,
    gff_gene."end" as end_position,
    gff_gene.strand
  from
    gff_gene
    LEFT JOIN gene_best_eggnog ON (gene_best_eggnog.gene_id = gff_gene.feature_id)
) TO '/opt/neo4j/import/picab-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Picab02_230926_at01_longest_no_TE_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source in ['PASN', 'manual', 'PASA']
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    eggnog_annotations as (
      select
        id as feature_id,
        eggnog_score as score,
        eggnog_go as go_terms
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Picab02_230926_at01_longest_representative_annotations_merged_sorted_non_redundant_panthers.tsv.gz',
          nullstr = 'NA'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.go_terms
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select distinct
    gene_id,
    trim(go_id) as go_id
  from
    gene_best_eggnog,
    unnest(str_split(go_terms, ',')) as t(go_id)
  where
    go_terms is not null
    and trim(go_id) like 'GO:%'
) TO '/opt/neo4j/import/picab-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Pinsy01_240308_at01_longest_no_TE.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source in ['PASN', 'manual', 'PASA']
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    gff_gene as (
      select * from gff_all where lower(feature_type) = 'gene'
    ),
    eggnog_annotations as (
      select
        id as feature_id,
        eggnog_description as description,
        eggnog_score as score,
        eggnog_preferred_name as gene_name
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Pinsy01_240308_at01_longest_representative_annotations_merged_sorted_non_redundant_panthers.tsv.gz',
          nullstr = 'NA'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.gene_name,
        eggnog_annotations.description
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select
    gff_gene.feature_id as gene_id,
    gene_best_eggnog.gene_name,
    gene_best_eggnog.description,
    gff_gene.seqid as chromosome,
    gff_gene.start as start_position,
    gff_gene."end" as end_position,
    gff_gene.strand
  from
    gff_gene
    LEFT JOIN gene_best_eggnog ON (gene_best_eggnog.gene_id = gff_gene.feature_id)
) TO '/opt/neo4j/import/pinsy-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Pinsy01_240308_at01_longest_no_TE.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source in ['PASN', 'manual', 'PASA']
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    eggnog_annotations as (
      select
        id as feature_id,
        eggnog_score as score,
        eggnog_go as go_terms
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Pinsy01_240308_at01_longest_representative_annotations_merged_sorted_non_redundant_panthers.tsv.gz',
          nullstr = 'NA'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.go_terms
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select distinct
    gene_id,
    trim(go_id) as go_id
  from
    gene_best_eggnog,
    unnest(str_split(go_terms, ',')) as t(go_id)
  where
    go_terms is not null
    and trim(go_id) like 'GO:%'
) TO '/opt/neo4j/import/pinsy-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Potra02_240916_genes_all_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source = 'maker'
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    gff_gene as (
      select * from gff_all where lower(feature_type) = 'gene'
    ),
    eggnog_annotations as (
      select
        query as feature_id,
        Description as description,
        score,
        Preferred_name as gene_name
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Potra02_240916_eggnog_annotation.tsv.gz',
          comment = '#',
          nullstr = '-'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.gene_name,
        eggnog_annotations.description
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select
    gff_gene.feature_id as gene_id,
    gene_best_eggnog.gene_name,
    gene_best_eggnog.description,
    gff_gene.seqid as chromosome,
    gff_gene.start as start_position,
    gff_gene."end" as end_position,
    gff_gene.strand
  from
    gff_gene
    LEFT JOIN gene_best_eggnog ON (gene_best_eggnog.gene_id = gff_gene.feature_id)
) TO '/opt/neo4j/import/potra-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Potra02_240916_genes_all_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source = 'maker'
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    eggnog_annotations as (
      select
        query as feature_id,
        score,
        GOs as go_terms
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Potra02_240916_eggnog_annotation.tsv.gz',
          comment = '#',
          nullstr = '-'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.go_terms
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select distinct
    gene_id,
    trim(go_id) as go_id
  from
    gene_best_eggnog,
    unnest(str_split(go_terms, ',')) as t(go_id)
  where
    go_terms is not null
    and trim(go_id) like 'GO:%'
) TO '/opt/neo4j/import/potra-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Tieton02_original_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source = 'funannotate'
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    gff_gene as (
      select * from gff_all where lower(feature_type) = 'gene'
    ),
    eggnog_annotations as (
      select
        query as feature_id,
        Description as description,
        score,
        Preferred_name as gene_name
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Tieton_v2p0_eggnog_annotation.tsv.gz',
          comment = '#',
          nullstr = '-'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.gene_name,
        eggnog_annotations.description
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select
    gff_gene.feature_id as gene_id,
    gene_best_eggnog.gene_name,
    gene_best_eggnog.description,
    gff_gene.seqid as chromosome,
    gff_gene.start as start_position,
    gff_gene."end" as end_position,
    gff_gene.strand
  from
    gff_gene
    LEFT JOIN gene_best_eggnog ON (gene_best_eggnog.gene_id = gff_gene.feature_id)
) TO '/opt/neo4j/import/pruav-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff_all as (
      select
        regexp_extract(attributes, 'ID=([^;]+)', 1) AS feature_id,
        regexp_extract(attributes, 'Parent=([^;]+)', 1) AS parent_id,
        *
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Tieton02_original_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where source = 'funannotate'
    ),
    gff_mrna as (
      select * from gff_all where lower(feature_type) = 'mrna'
    ),
    eggnog_annotations as (
      select
        query as feature_id,
        score,
        GOs as go_terms
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/Tieton_v2p0_eggnog_annotation.tsv.gz',
          comment = '#',
          nullstr = '-'
        )
      QUALIFY row_number() OVER (PARTITION BY feature_id ORDER BY score DESC) = 1
    ),
    gene_best_eggnog as (
      select
        gff_mrna.parent_id as gene_id,
        eggnog_annotations.go_terms
      from
        gff_mrna
        INNER JOIN eggnog_annotations ON (eggnog_annotations.feature_id = gff_mrna.feature_id)
      QUALIFY row_number() OVER (PARTITION BY gff_mrna.parent_id ORDER BY eggnog_annotations.score DESC) = 1
    )
  select distinct
    gene_id,
    trim(go_id) as go_id
  from
    gene_best_eggnog,
    unnest(str_split(go_terms, ',')) as t(go_id)
  where
    go_terms is not null
    and trim(go_id) like 'GO:%'
) TO '/opt/neo4j/import/pruav-gene-go.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff as (
      select
        NULLIF(regexp_extract(attributes, 'ID=([^;]+)', 1), '') AS gene_id,
        NULLIF(trim(regexp_extract(attributes, 'description=([^;\[]+)', 1)), '') AS description
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/TAIR10_araport11_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where
        lower(feature_type) = 'gene'
        AND source = 'araport11'
    )
  select gene_id, description
  from gff
  where description is not null
) TO '/opt/neo4j/import/arath-araport11-functional-descriptions.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff as (
      select
        NULLIF(regexp_extract(attributes, 'ID=([^;]+)', 1), '') AS gene_id,
        NULLIF(regexp_extract(attributes, 'Name=([^;]+)', 1), '') AS gene_name,
        seqid,
        start,
        "end",
        strand
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/TAIR10_araport11_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where
        lower(feature_type) = 'gene'
        AND source = 'araport11'
    ),
    functional_descriptions as (
      select gene_id, description
      from read_csv(
        '/opt/neo4j/import/arath-araport11-functional-descriptions.csv',
        delim = '\t',
        header = true
      )
    )
  select
    gff.gene_id,
    gff.gene_name,
    functional_descriptions.description,
    gff.seqid as chromosome,
    gff.start as start_position,
    gff."end" as end_position,
    gff.strand
  from
    gff
    LEFT JOIN functional_descriptions ON functional_descriptions.gene_id = gff.gene_id
) TO '/opt/neo4j/import/arath-araport11-gene-records.csv' (HEADER, DELIMITER '\t');

COPY (
  with
    gff as (
      select
        NULLIF(regexp_extract(attributes, 'ID=([^;]+)', 1), '') AS gene_id,
        NULLIF(regexp_extract(attributes, 'Name=([^;]+)', 1), '') AS gene_name,
        seqid,
        start,
        "end",
        strand
      from
        read_csv(
          'https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/TAIR10_GFF3_genes_sorted.gff3.gz',
          header = false,
          delim = '\t',
          comment = '#',
          columns = {
            'seqid': 'VARCHAR',
            'source': 'VARCHAR',
            'feature_type': 'VARCHAR',
            'start': 'BIGINT',
            'end': 'BIGINT',
            'score': 'VARCHAR',
            'strand': 'VARCHAR',
            'phase': 'VARCHAR',
            'attributes': 'VARCHAR'
          },
          auto_detect = false,
          nullstr = '.'
        )
      where
        lower(feature_type) = 'gene'
        AND source = 'TAIR10'
    ),
    functional_descriptions as (
      SELECT
        regexp_replace(Model_name, '\.[0-9]+$', '') AS gene_id,
        Short_description as description
      FROM
        read_csv('https://north-1.cloud.snic.se:8080/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc/plantgenie-knowledge/TAIR10_functional_descriptions')
      QUALIFY
        row_number() OVER (
          PARTITION BY regexp_replace(Model_name, '\.[0-9]+$', '')
          ORDER BY Model_name
        ) = 1
    )
  select
    gff.gene_id,
    gff.gene_name,
    functional_descriptions.description,
    gff.seqid as chromosome,
    gff.start as start_position,
    gff."end" as end_position,
    gff.strand
  from
    gff
    LEFT JOIN functional_descriptions ON functional_descriptions.gene_id = gff.gene_id
) TO '/opt/neo4j/import/arath-tair10-gene-records.csv' (HEADER, DELIMITER '\t');

CREATE OR REPLACE TEMP TABLE go_nodes AS
  SELECT *
  FROM read_ndjson_auto('/tmp/knowledge-builder/go-basic-nodes.ndjson', union_by_name = true)
  WHERE type = 'CLASS'
    AND id LIKE '%/GO_%';

CREATE OR REPLACE TEMP TABLE go_edges AS
  SELECT *
  FROM read_ndjson_auto('/tmp/knowledge-builder/go-basic-edges.ndjson', union_by_name = true)
  WHERE pred IN ('is_a', 'http://purl.obolibrary.org/obo/BFO_0000050')
    AND sub LIKE '%/GO_%'
    AND obj LIKE '%/GO_%';

COPY (
  SELECT
    'GO:' || regexp_extract(id, 'GO_([0-9]+)', 1) AS id,
    lbl AS name,
    list_extract(
      list_filter(
        meta.basicPropertyValues,
        bpv -> bpv.pred = 'http://www.geneontology.org/formats/oboInOwl#hasOBONamespace'
      ), 1
    ).val AS namespace,
    meta.definition.val AS definition,
    coalesce(meta.deprecated, false) AS is_obsolete
  FROM go_nodes
) TO '/opt/neo4j/import/go-terms.csv' (HEADER, DELIMITER '\t');

COPY (
  SELECT
    'GO:' || regexp_extract(sub, 'GO_([0-9]+)', 1) AS from_id,
    'GO:' || regexp_extract(obj, 'GO_([0-9]+)', 1) AS to_id,
    CASE pred
      WHEN 'is_a' THEN 'IS_A'
      WHEN 'http://purl.obolibrary.org/obo/BFO_0000050' THEN 'PART_OF'
    END AS type
  FROM go_edges
) TO '/opt/neo4j/import/go-edges.csv' (HEADER, DELIMITER '\t');
