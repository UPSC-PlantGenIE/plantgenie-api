from knowledge_builder.catalog.types import CatalogBuilder
from knowledge_builder.catalog.constants import (
    SWIFT_BUCKET,
    DERIVED_PREFIX,
)


def register_betpe(cb: CatalogBuilder) -> None:
    gff = cb.static_asset(
        id="betpe::gff",
        kind="gff",
        bucket_uri=f"{SWIFT_BUCKET}/Bepen_v1p2_coge_sorted.gff3.gz",
        source_url=(
            "https://genomevolution.org/coge/api/v1/downloads/"
            "?gid=68624"
            "&filename=Betula_pendula_subsp._pendula_annos1"
            "-cds0-id_typenum-nu1-upa1-add_chr0.gid68624.gff"
        ),
    )
    genome = cb.static_asset(
        id="betpe::genome",
        kind="fasta",
        bucket_uri=f"{SWIFT_BUCKET}/Bepen_v1p2_genome.fa.gz",
        source_url=(
            "https://genomevolution.org/coge/api/v1"
            "/genomes/68624/sequence"
        ),
    )
    eggnog = cb.static_asset(
        id="betpe::eggnog-tsv",
        kind="eggnog_tsv",
        bucket_uri=(
            f"{SWIFT_BUCKET}"
            "/Bepen_v1p2_eggnog_annotation.tsv.gz"
        ),
    )

    gene_records = cb.derived_asset(
        id="betpe::gene-records-csv",
        kind="gene_records_csv",
        bucket_uri=f"{DERIVED_PREFIX}/betpe-gene-records.csv",
    )
    gene_go = cb.derived_asset(
        id="betpe::gene-go-csv",
        kind="gene_go_csv",
        bucket_uri=f"{DERIVED_PREFIX}/betpe-gene-go.csv",
    )

    cb.step(
        id="betpe-gene-records",
        command="kb run-sql steps/sql/betpe-gene-records.sql",
        body_path="steps/sql/betpe-gene-records.sql",
        reads={"gff": gff, "eggnog": eggnog},
        writes={"records": gene_records},
    )
    cb.step(
        id="betpe-gene-go",
        command="kb run-sql steps/sql/betpe-gene-go.sql",
        body_path="steps/sql/betpe-gene-go.sql",
        reads={"gff": gff, "eggnog": eggnog},
        writes={"gene_go": gene_go},
    )

    cb.step(
        id="load-betpe-genes",
        command=(
            "kb run-cypher steps/cypher/load-betpe-genes.cypher"
        ),
        body_path="steps/cypher/load-betpe-genes.cypher",
        reads={"records": gene_records},
        writes={},
    )
    cb.step(
        id="load-betpe-gene-go",
        command=(
            "kb run-cypher steps/cypher/load-betpe-gene-go.cypher"
        ),
        body_path="steps/cypher/load-betpe-gene-go.cypher",
        reads={"gene_go": gene_go},
        writes={},
    )

    cb.annotation_link(
        annotation_id="betpe-v1.2",
        role="gene_records",
        asset=gene_records,
    )
    cb.annotation_link(
        annotation_id="betpe-v1.2",
        role="gene_go",
        asset=gene_go,
    )
