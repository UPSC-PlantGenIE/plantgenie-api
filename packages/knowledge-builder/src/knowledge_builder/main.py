from __future__ import annotations

import json
import os
import subprocess
import time
from ftplib import FTP
from pathlib import Path
from urllib.parse import urlsplit

import duckdb
import httpx
import typer
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase
from shared.services.openstack import SwiftClient

REQUIRED_ENV = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD")
SYNC_REQUIRED_ENV = (
    "OS_AUTH_TYPE",
    "OS_AUTH_URL",
    "OS_APPLICATION_CREDENTIAL_ID",
    "OS_APPLICATION_CREDENTIAL_SECRET",
)
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = PACKAGE_ROOT.parent.parent
CONFIG_PATH = PACKAGE_ROOT / "knowledge.yaml"
CYPHER_DIR = Path(__file__).parent / "cypher"
SQL_DIR = Path(__file__).parent / "sql"
load_dotenv(REPO_ROOT / ".env.shared")
load_dotenv()

app = typer.Typer()


def fetch_arath_genome(client, container, object_name, source_url):
    local = Path("/tmp/knowledge-builder/arath-genome.fa.gz")
    local.parent.mkdir(parents=True, exist_ok=True)
    typer.echo(f"downloading arath genome from {source_url}")
    with httpx.stream(
        "GET", source_url, follow_redirects=True, verify=False
    ) as response:
        response.raise_for_status()
        with local.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    typer.echo(f"uploading {object_name} to {container}")
    client.upload(container, object_name, local)
    local.unlink()


def fetch_betpe_genome(client, container, object_name, source_url):
    local = Path("/tmp/knowledge-builder/betpe-genome.fa")
    local.parent.mkdir(parents=True, exist_ok=True)
    typer.echo(f"downloading betpe genome from {source_url}")
    with httpx.stream("GET", source_url, follow_redirects=True) as response:
        response.raise_for_status()
        with local.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    typer.echo(f"uploading {object_name} to {container}")
    client.upload(container, object_name, local)
    local.unlink()


def fetch_potra_genome(client, container, object_name, source_url):
    local = Path("/tmp/knowledge-builder/potra-genome.fasta.gz")
    local.parent.mkdir(parents=True, exist_ok=True)
    typer.echo(f"downloading potra genome from {source_url}")
    parsed = urlsplit(source_url)
    with FTP() as ftp:
        ftp.connect(parsed.hostname, parsed.port or 21)
        ftp.login()
        with local.open("wb") as f:
            ftp.retrbinary(f"RETR {parsed.path}", f.write)
    typer.echo(f"uploading {object_name} to {container}")
    client.upload(container, object_name, local)
    local.unlink()


def fetch_pruav_genome(client, container, object_name, source_url):
    local = Path("/tmp/knowledge-builder/pruav-genome.fasta.gz")
    local.parent.mkdir(parents=True, exist_ok=True)
    typer.echo(f"downloading pruav genome from {source_url}")
    with httpx.stream(
        "GET", source_url, follow_redirects=True, verify=False
    ) as response:
        response.raise_for_status()
        with local.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    typer.echo(f"uploading {object_name} to {container}")
    client.upload(container, object_name, local)
    local.unlink()


def build_betpe_v1_v1_2_gffread(client, container):
    work = Path("/tmp/knowledge-builder/betpe-gffread")
    work.mkdir(parents=True, exist_ok=True)

    genome = work / "Bepen_v1p2_genome.fa"
    gff_gz = work / "Bepen_v1p2_coge_sorted.gff3.gz"
    gff = work / "Bepen_v1p2_coge_sorted.gff3"

    typer.echo(f"downloading {genome.name}")
    client.download_object(container, genome.name, genome)
    typer.echo(f"downloading {gff_gz.name}")
    client.download_object(container, gff_gz.name, gff_gz)

    typer.echo(f"stripping lcl| prefix from {genome.name} headers")
    subprocess.run(["sed", "-i", "s/^>lcl|/>/", str(genome)], check=True)

    typer.echo(f"decompressing {gff_gz.name}")
    subprocess.run(["gunzip", "-f", "-k", str(gff_gz)], check=True)

    cds = work / "Bepen_v1p2_cds.fa"
    mrna = work / "Bepen_v1p2_mrna.fa"
    protein = work / "Bepen_v1p2_protein.fa"

    typer.echo("running gffread")
    subprocess.run(
        [
            "gffread", str(gff),
            "-g", str(genome),
            "-x", str(cds),
            "-w", str(mrna),
            "-y", str(protein),
        ],
        check=True,
    )

    for output in (cds, mrna, protein):
        bgz = Path(str(output) + ".gz")
        fai = Path(str(bgz) + ".fai")
        gzi = Path(str(bgz) + ".gzi")

        typer.echo(f"bgzip {output.name}")
        subprocess.run(["bgzip", "-f", str(output)], check=True)

        typer.echo(f"samtools faidx {bgz.name}")
        subprocess.run(["samtools", "faidx", str(bgz)], check=True)

        for path in (bgz, fai, gzi):
            typer.echo(f"uploading {path.name}")
            client.upload(container, path.name, path)


STEP_BUILDERS = {
    "betpe/v1/v1.2/build-gffread": build_betpe_v1_v1_2_gffread,
}


@app.command(name="sync")
def sync() -> None:
    missing = [name for name in SYNC_REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            f"Required env vars not set: {', '.join(missing)}"
        )

    config = yaml.safe_load(CONFIG_PATH.read_text())
    bucket = config["bucket"]
    container = bucket.rsplit("/", 1)[1]

    client = SwiftClient(
        openstack_auth_type=os.environ["OS_AUTH_TYPE"],
        openstack_auth_url=os.environ["OS_AUTH_URL"],
        application_credential_id=os.environ["OS_APPLICATION_CREDENTIAL_ID"],
        application_credential_secret=os.environ["OS_APPLICATION_CREDENTIAL_SECRET"],
    )
    typer.echo(f"authenticated to {client.storage_service_url}")

    bucket_objects = {o["name"] for o in client.list_objects(container)}
    typer.echo(f"{container}: {len(bucket_objects)} objects in bucket")

    assets = []
    for asset in (config.get("shared") or {}).get("assets") or []:
        if asset.get("object"):
            assets.append(
                (asset["id"], asset["object"], asset.get("source_url"))
            )
    for taxon in config["taxa"]:
        taxon_id = taxon["abbreviation"]
        for assembly in taxon.get("assemblies") or []:
            assembly_id = f"{taxon_id}/{assembly['version']}"
            for asset in assembly.get("assets") or []:
                if asset.get("object"):
                    assets.append(
                        (
                            f"{assembly_id}/{asset['name']}",
                            asset["object"],
                            asset.get("source_url"),
                        )
                    )
            for annotation in assembly.get("annotations") or []:
                annotation_id = f"{assembly_id}/{annotation['slug']}"
                for asset in annotation.get("assets") or []:
                    if asset.get("object"):
                        assets.append(
                            (
                                f"{annotation_id}/{asset['name']}",
                                asset["object"],
                                asset.get("source_url"),
                            )
                        )

    present = [a for a in assets if a[1] in bucket_objects]
    absent = [a for a in assets if a[1] not in bucket_objects]
    typer.echo(
        f"declared in yaml: {len(assets)} "
        f"({len(present)} present, {len(absent)} missing)"
    )
    for asset_id, obj, src in absent:
        typer.echo(
            f"  MISSING  {asset_id} -> {obj}  (source: {src or '—'})"
        )
        if asset_id == "pruav/v2/genome":
            fetch_pruav_genome(client, container, obj, src)
        if asset_id == "potra/v2/genome":
            fetch_potra_genome(client, container, obj, src)
        if asset_id == "betpe/v1/genome":
            fetch_betpe_genome(client, container, obj, src)
        if asset_id == "arath/tair10/genome":
            fetch_arath_genome(client, container, obj, src)


@app.command(name="build")
def build() -> None:
    missing = [
        name
        for name in (*REQUIRED_ENV, *SYNC_REQUIRED_ENV)
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(
            f"Required env vars not set: {', '.join(missing)}"
        )

    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]

    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        typer.echo(f"connected to {uri} as {user}")

        config = yaml.safe_load(CONFIG_PATH.read_text())
        typer.echo(
            f"loaded {CONFIG_PATH.name}: "
            f"{len(config['taxa'])} taxa, "
            f"{len(config.get('steps', []))} build steps, "
            f"{len(config.get('loads', []))} load steps"
        )

        bucket = config["bucket"]

        taxon_rows = []
        assembly_rows = []
        annotation_rows = []
        asset_rows = []
        annotation_from_rows = []
        assembly_from_rows = []

        for asset in (config.get("shared") or {}).get("assets") or []:
            object_name = asset.get("object")
            asset_rows.append(
                {
                    "id": asset["id"],
                    "name": asset.get("name"),
                    "format": asset["format"],
                    "object": object_name,
                    "bucketUri": f"{bucket}/{object_name}" if object_name else None,
                    "sourceUrl": asset.get("source_url"),
                }
            )

        for taxon in config["taxa"]:
            taxon_id = taxon["abbreviation"]
            taxon_rows.append(
                {
                    "id": taxon_id,
                    "abbreviation": taxon["abbreviation"],
                    "scientificName": taxon["scientificName"],
                    "alias": taxon["alias"],
                    "commonName": taxon["commonName"],
                }
            )
            for assembly in taxon.get("assemblies") or []:
                assembly_id = f"{taxon_id}/{assembly['version']}"
                publication_date = assembly.get("publicationDate")
                assembly_rows.append(
                    {
                        "id": assembly_id,
                        "taxonId": taxon_id,
                        "version": assembly["version"],
                        "versionName": assembly["versionName"],
                        "published": assembly.get("published", False),
                        "publicationDate": str(publication_date)
                        if publication_date
                        else None,
                        "doi": assembly.get("doi"),
                    }
                )
                for asset in assembly.get("assets") or []:
                    asset_id = f"{assembly_id}/{asset['name']}"
                    object_name = asset.get("object")
                    asset_rows.append(
                        {
                            "id": asset_id,
                            "name": asset["name"],
                            "format": asset["format"],
                            "object": object_name,
                            "bucketUri": f"{bucket}/{object_name}" if object_name else None,
                            "sourceUrl": asset.get("source_url"),
                        }
                    )
                    assembly_from_rows.append(
                        {"assetId": asset_id, "assemblyId": assembly_id}
                    )
                for annotation in assembly.get("annotations") or []:
                    annotation_id = f"{assembly_id}/{annotation['slug']}"
                    annotation_rows.append(
                        {
                            "id": annotation_id,
                            "assemblyId": assembly_id,
                            "slug": annotation["slug"],
                            "geneCount": annotation["geneCount"],
                            "isDefault": annotation["isDefault"],
                        }
                    )
                    for asset in annotation.get("assets") or []:
                        asset_id = f"{annotation_id}/{asset['name']}"
                        object_name = asset.get("object")
                        asset_rows.append(
                            {
                                "id": asset_id,
                                "name": asset["name"],
                                "format": asset["format"],
                                "object": object_name,
                                "bucketUri": f"{bucket}/{object_name}" if object_name else None,
                                "sourceUrl": asset.get("source_url"),
                            }
                        )
                        annotation_from_rows.append(
                            {"assetId": asset_id, "annotationId": annotation_id}
                        )
            for use in taxon.get("uses") or []:
                used_id = use["assembly"]
                matching = next(
                    (a for a in assembly_rows if a["id"] == used_id), None
                )
                if matching is None:
                    raise RuntimeError(
                        f"taxon {taxon_id} 'uses' assembly {used_id} "
                        f"which is not declared"
                    )
                assembly_rows.append({**matching, "taxonId": taxon_id})

        build_step_rows = []
        build_read_rows = []
        build_write_rows = []
        for step in config.get("steps", []) or []:
            build_step_rows.append({"id": step["id"]})
            for read_id in step.get("reads", []) or []:
                build_read_rows.append({"assetId": read_id, "stepId": step["id"]})
            for write in step.get("writes", []) or []:
                object_name = write.get("object")
                asset_rows.append(
                    {
                        "id": write["id"],
                        "name": None,
                        "format": write.get("format"),
                        "object": object_name,
                        "bucketUri": f"{bucket}/{object_name}" if object_name else None,
                        "sourceUrl": None,
                    }
                )
                build_write_rows.append({"stepId": step["id"], "assetId": write["id"]})

        load_step_rows = []
        load_read_rows = []
        requires_rows = []
        for load in config.get("loads", []) or []:
            load_step_rows.append({"id": load["id"]})
            for read_id in load.get("reads", []) or []:
                load_read_rows.append({"assetId": read_id, "stepId": load["id"]})
            for required_id in load.get("requires", []) or []:
                requires_rows.append({"fromId": load["id"], "toId": required_id})

        domain_cypher = (CYPHER_DIR / "merge_domain.cypher").read_text()
        build_cypher = (CYPHER_DIR / "merge_build.cypher").read_text()
        domain_statements = [
            s for s in (stmt.strip() for stmt in domain_cypher.split(";")) if s
        ]
        build_statements = [
            s for s in (stmt.strip() for stmt in build_cypher.split(";")) if s
        ]
        params = {
            "taxon_rows": taxon_rows,
            "assembly_rows": assembly_rows,
            "annotation_rows": annotation_rows,
            "asset_rows": asset_rows,
            "annotation_from_rows": annotation_from_rows,
            "assembly_from_rows": assembly_from_rows,
            "build_step_rows": build_step_rows,
            "build_read_rows": build_read_rows,
            "build_write_rows": build_write_rows,
            "load_step_rows": load_step_rows,
            "load_read_rows": load_read_rows,
            "requires_rows": requires_rows,
        }
        with driver.session() as session:
            for statement in domain_statements:
                session.run(statement, params)
            for statement in build_statements:
                session.run(statement, params)
        typer.echo(
            f"merged domain half: {len(taxon_rows)} taxa, "
            f"{len(assembly_rows)} assemblies, {len(annotation_rows)} annotations"
        )
        typer.echo(
            f"merged build half: {len(asset_rows)} assets "
            f"({len(annotation_from_rows) + len(assembly_from_rows)} FROM edges), "
            f"{len(build_step_rows)} build steps "
            f"({len(build_read_rows)} READ_BY, {len(build_write_rows)} WRITES), "
            f"{len(load_step_rows)} load steps "
            f"({len(load_read_rows)} READ_BY, {len(requires_rows)} REQUIRES)"
        )

        container = bucket.rsplit("/", 1)[1]
        client = SwiftClient(
            openstack_auth_type=os.environ["OS_AUTH_TYPE"],
            openstack_auth_url=os.environ["OS_AUTH_URL"],
            application_credential_id=os.environ["OS_APPLICATION_CREDENTIAL_ID"],
            application_credential_secret=os.environ["OS_APPLICATION_CREDENTIAL_SECRET"],
        )
        for step in config.get("steps", []) or []:
            builder = STEP_BUILDERS.get(step["id"])
            if builder is None:
                continue
            typer.echo(f"running {step['id']}")
            builder(client, container)

        go_dir = Path("/tmp/knowledge-builder")
        go_dir.mkdir(parents=True, exist_ok=True)
        go_json = go_dir / "go-basic.json"
        go_nodes_ndjson = go_dir / "go-basic-nodes.ndjson"
        go_edges_ndjson = go_dir / "go-basic-edges.ndjson"

        typer.echo("go-basic.json: download started")
        t0 = time.perf_counter()
        with httpx.stream(
            "GET",
            "https://current.geneontology.org/ontology/go-basic.json",
            follow_redirects=True,
        ) as response:
            response.raise_for_status()
            with go_json.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
        typer.echo(
            f"go-basic.json: download finished "
            f"({go_json.stat().st_size:,} bytes, {time.perf_counter() - t0:.1f}s)"
        )

        typer.echo("go-basic.json: parse + ndjson conversion started")
        t0 = time.perf_counter()
        with go_json.open() as f:
            data = json.load(f)
        graph = data["graphs"][0]
        with go_nodes_ndjson.open("w") as f:
            for node in graph["nodes"]:
                f.write(json.dumps(node) + "\n")
        with go_edges_ndjson.open("w") as f:
            for edge in graph["edges"]:
                f.write(json.dumps(edge) + "\n")
        typer.echo(
            f"go-basic.json: parse + ndjson conversion finished "
            f"({len(graph['nodes']):,} nodes, {len(graph['edges']):,} edges, "
            f"{time.perf_counter() - t0:.1f}s)"
        )

        build_sql = (SQL_DIR / "build.sql").read_text()
        typer.echo("build.sql: started")
        t0 = time.perf_counter()
        con = duckdb.connect()
        con.execute("PRAGMA enable_progress_bar")
        con.execute(build_sql)
        con.close()
        typer.echo(f"build.sql: finished ({time.perf_counter() - t0:.1f}s)")

        load_cypher = (CYPHER_DIR / "load.cypher").read_text()
        load_statements = [
            s for s in (stmt.strip() for stmt in load_cypher.split(";")) if s
        ]
        typer.echo(f"load.cypher: started ({len(load_statements)} statements)")
        t0 = time.perf_counter()
        with driver.session() as session:
            for statement in load_statements:
                session.run(statement)
        typer.echo(f"load.cypher: finished ({time.perf_counter() - t0:.1f}s)")

        typer.echo("")
        typer.echo("graph report:")
        with driver.session() as session:
            for label in (
                "Taxon", "Assembly", "Annotation", "Asset",
                "BuildStep", "LoadStep", "Gene", "GoTerm",
            ):
                n = session.run(f"MATCH (n:{label}) RETURN count(n) AS n").single()["n"]
                typer.echo(f"  {label:12} {n:>10,}")
            typer.echo("")
            rows = session.run("""
                MATCH (ann:Annotation)
                OPTIONAL MATCH (g:Gene)-[:OF]->(ann)
                OPTIONAL MATCH (g)-[r:HAS_GO]->(:GoTerm)
                RETURN ann.id AS annotation, count(DISTINCT g) AS genes, count(r) AS has_go
                ORDER BY ann.id
            """).data()
            typer.echo(f"  {'annotation':30} {'genes':>10} {'has_go':>12}")
            for r in rows:
                typer.echo(f"  {r['annotation']:30} {r['genes']:>10,} {r['has_go']:>12,}")
