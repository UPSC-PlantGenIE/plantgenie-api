from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import typer
import yaml
from neo4j import Driver, GraphDatabase, Session

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge.yaml"


@dataclass
class Annotation:
    id: str
    slug: str
    gene_count: int
    is_default: bool


@dataclass
class Assembly:
    id: str
    version: str
    version_name: str
    published: bool
    publication_date: str | None
    doi: str | None
    annotations: list[Annotation] = field(default_factory=list)


@dataclass
class Taxon:
    id: str
    abbreviation: str
    scientific_name: str
    alias: str
    common_name: str
    assemblies: list[Assembly] = field(default_factory=list)


@dataclass
class Config:
    bucket: str
    taxa: list[Taxon]


def load_config(path: Path) -> Config:
    raw = yaml.safe_load(path.read_text())
    taxa: list[Taxon] = []
    for t in raw.get("taxa", []):
        abbr = t["abbreviation"]
        assemblies: list[Assembly] = []
        for a in t.get("assemblies", []) or []:
            assembly_id = f"{abbr}/{a['version']}"
            annotations = [
                Annotation(
                    id=f"{assembly_id}/{ann['slug']}",
                    slug=ann["slug"],
                    gene_count=ann["geneCount"],
                    is_default=ann["isDefault"],
                )
                for ann in a.get("annotations", []) or []
            ]
            assemblies.append(
                Assembly(
                    id=assembly_id,
                    version=a["version"],
                    version_name=a["versionName"],
                    published=a.get("published", False),
                    publication_date=str(a["publicationDate"]) if a.get("publicationDate") else None,
                    doi=a.get("doi"),
                    annotations=annotations,
                )
            )
        taxa.append(
            Taxon(
                id=abbr,
                abbreviation=abbr,
                scientific_name=t["scientificName"],
                alias=t["alias"],
                common_name=t["commonName"],
                assemblies=assemblies,
            )
        )
    return Config(bucket=raw["bucket"], taxa=taxa)


def connect(uri: str, user: str, password: str) -> Driver:
    return GraphDatabase.driver(uri, auth=(user, password))


CONSTRAINTS = [
    "CREATE CONSTRAINT taxon_id IF NOT EXISTS FOR (n:Taxon) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT assembly_id IF NOT EXISTS FOR (n:Assembly) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT annotation_id IF NOT EXISTS FOR (n:Annotation) REQUIRE n.id IS UNIQUE",
]


def ensure_constraints(session: Session) -> None:
    for stmt in CONSTRAINTS:
        session.run(stmt)


TAXON_CYPHER = """
UNWIND $rows AS row
MERGE (n:Taxon {id: row.id})
SET n.abbreviation = row.abbreviation,
    n.scientificName = row.scientificName,
    n.alias = row.alias,
    n.commonName = row.commonName
"""

ASSEMBLY_CYPHER = """
UNWIND $rows AS row
MATCH (t:Taxon {id: row.taxonId})
MERGE (a:Assembly {id: row.id})
SET a.version = row.version,
    a.versionName = row.versionName,
    a.published = row.published,
    a.publicationDate = row.publicationDate,
    a.doi = row.doi
MERGE (a)-[:OF]->(t)
"""

ANNOTATION_CYPHER = """
UNWIND $rows AS row
MATCH (a:Assembly {id: row.assemblyId})
MERGE (n:Annotation {id: row.id})
SET n.slug = row.slug,
    n.geneCount = row.geneCount,
    n.isDefault = row.isDefault
MERGE (n)-[:OF]->(a)
"""


def seed_domain(session: Session, config: Config) -> tuple[int, int, int]:
    taxon_rows = [
        {
            "id": t.id,
            "abbreviation": t.abbreviation,
            "scientificName": t.scientific_name,
            "alias": t.alias,
            "commonName": t.common_name,
        }
        for t in config.taxa
    ]
    assembly_rows = [
        {
            "id": a.id,
            "taxonId": t.id,
            "version": a.version,
            "versionName": a.version_name,
            "published": a.published,
            "publicationDate": a.publication_date,
            "doi": a.doi,
        }
        for t in config.taxa
        for a in t.assemblies
    ]
    annotation_rows = [
        {
            "id": ann.id,
            "assemblyId": a.id,
            "slug": ann.slug,
            "geneCount": ann.gene_count,
            "isDefault": ann.is_default,
        }
        for t in config.taxa
        for a in t.assemblies
        for ann in a.annotations
    ]

    session.execute_write(lambda tx: tx.run(TAXON_CYPHER, rows=taxon_rows))
    session.execute_write(lambda tx: tx.run(ASSEMBLY_CYPHER, rows=assembly_rows))
    session.execute_write(lambda tx: tx.run(ANNOTATION_CYPHER, rows=annotation_rows))

    return len(taxon_rows), len(assembly_rows), len(annotation_rows)


load_app = typer.Typer(help="Load steps.", no_args_is_help=True)


@load_app.command("domain")
def load_domain(
    config_path: Path = typer.Option(
        DEFAULT_CONFIG_PATH, "--config", "-c", help="Path to knowledge.yaml."
    ),
    uri: str = typer.Option("bolt://localhost:7687", envvar="NEO4J_URI"),
    user: str = typer.Option("neo4j", envvar="NEO4J_USER"),
    password: str = typer.Option("guest123", envvar="NEO4J_PASSWORD"),
) -> None:
    config = load_config(config_path)
    with connect(uri, user, password) as driver, driver.session() as session:
        ensure_constraints(session)
        taxa, assemblies, annotations = seed_domain(session, config)
    typer.echo(
        f"Seeded {taxa} taxa, {assemblies} assemblies, {annotations} annotations."
    )
