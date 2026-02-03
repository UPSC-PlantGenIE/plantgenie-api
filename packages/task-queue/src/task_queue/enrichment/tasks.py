import mimetypes
import os
from pathlib import Path

import duckdb
from celery import Task
from go_enrich.main import main
from shared.constants import GO_ENRICH_BUCKET_NAME
from shared.services.openstack import (
    SwiftClient,
    SwiftUploadableObject,
)

from task_queue.celery import app
from task_queue.enrichment.models import GoEnrichPipelineArgs
from task_queue.tasks import (
    PathValidationTask,
)


@app.task(
    name="enrichment.verify_target",
    base=PathValidationTask,
    files_to_validate={"target_path": "Target Genes"},
)
def verify_target_genes_file(target_path: str) -> str:
    # sql to verify genes in genome?
    return target_path


@app.task(
    name="enrichment.verify_background",
    base=PathValidationTask,
    files_to_validate={"background_path": "Background Genes"},
)
def verify_background_genes_file(background_path: str) -> str:
    # sql to verify genes in genome?
    return background_path


@app.task(
    name="enrichment.run_pipeline", typing=True, pydantic=True, bind=True
)
def run_go_enrichment_pipeline(self: Task, args: GoEnrichPipelineArgs):
    resolved_parent_path = (
        Path(args.target_path).parent.resolve(True).as_posix()
    )
    resolved_target_path = Path(args.target_path).resolve(True).as_posix()
    resolved_background_path = (
        Path(args.background_path).resolve(True).as_posix()
    )
    resolved_database_path = (
        (Path(os.environ["DATA_PATH"]) / os.environ["DATABASE_NAME"])
        .resolve(True)
        .as_posix()
    )

    with duckdb.connect(
        resolved_database_path, read_only=True
    ) as database_connnection:
        placeholders = ", ".join("?" for _ in args.node_types)

        query_relation = database_connnection.sql(
            f"""
            SELECT id
            FROM go_nodes
            WHERE go_type IN ({placeholders});
            """,
            params=args.node_types,
        )

        nodes_output_path = (
            f"{resolved_parent_path}/{self.request.id}-go-nodes.tsv"
        )
        query_relation.write_csv(nodes_output_path, header=False, sep="\t")

        query_relation = database_connnection.sql(
            f"""
            SELECT e.go_from, e.go_to FROM go_edges e
                JOIN go_nodes n_from ON n_from.id = e.go_from
                JOIN go_nodes n_to   ON n_to.id   = e.go_to
            WHERE n_from.go_type IN ({placeholders})
                AND n_to.go_type IN ({placeholders});
            """,
            params=args.node_types * 2,
        )

        edges_output_path = (
            f"{resolved_parent_path}/{self.request.id}-go-edges.tsv"
        )
        query_relation.write_csv(edges_output_path, header=False, sep="\t")

        query_relation = database_connnection.sql(
            """
            WITH target_genes AS (
                SELECT column0 AS gene_id
                    FROM read_csv(?, header = false, sep = '\t')
            ),
            background_genes AS (
                SELECT column0 AS gene_id
                    FROM read_csv(?, header = false, sep = '\t')
            ),
            all_genes AS (
                SELECT gene_id FROM target_genes
                UNION
                SELECT gene_id FROM background_genes
            )
            SELECT g.gene_id, g.go_term
                FROM go_terms_per_gene g
            JOIN all_genes a ON a.gene_id = g.gene_id
                WHERE g.genome_id = ?;
            """,
            params=[
                resolved_target_path,
                resolved_background_path,
                args.genome_id,
            ],
        )
        mapping_output_path = f"{resolved_parent_path}/{self.request.id}-genes-to-go-mapping.tsv"
        query_relation.write_csv(
            mapping_output_path, header=False, sep="\t"
        )

        results_output_path = (
            Path(resolved_parent_path)
            / f"{self.request.id}-go-enrichment-results.tsv"
        )

        main(
            Path(resolved_target_path),
            Path(resolved_background_path),
            Path(nodes_output_path),
            Path(edges_output_path),
            Path(mapping_output_path),
            base_fdr=args.base_fdr,
            min_genes_per_node=args.min_genes_per_node,
            output=results_output_path,
        )

        paths_to_upload = [
            resolved_target_path,
            resolved_background_path,
            nodes_output_path,
            edges_output_path,
            mapping_output_path,
            results_output_path.as_posix(),
        ]

        uploadables = [
            SwiftUploadableObject(
                local_path=p,
                object_name=Path(p).name,
                content_type=mimetypes.guess_type(Path(p).name)[0],
            )
            for p in paths_to_upload
        ]

        SwiftClient().upload_objects(
            container=GO_ENRICH_BUCKET_NAME, objects=uploadables
        )
