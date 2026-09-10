"""Generate blast-databases.csv for blast-database-load.cypher.

Every BLAST database has exactly one .njs/.pjs metadata file, so globbing
those finds the databases that really exist. Genome databases sit under an
assembly directory, the rest under an annotation directory.
"""

import csv
from pathlib import Path

ROOT = Path("/opt/data/plantgenie-knowledge")
OUTPUT = Path("/opt/neo4j/import/blast-databases.csv")
SKIPPED_TAXA = {"arath", "global"}

DATABASES = {
    "genome.fa": ("genome", "Genome"),
    "coding-sequences.fa": ("cds", "Coding sequences"),
    "transcript-sequences.fa": ("transcript", "Transcripts"),
    "amino-acid-sequences.fa": ("protein", "Proteins"),
}

rows = []

for metadata in ROOT.glob("**/blast/*/*.[np]js"):
    parts = metadata.relative_to(ROOT).parts
    taxon, owner_versions = parts[0], parts[1:-3]

    if taxon in SKIPPED_TAXA:
        continue

    base = metadata.name.removesuffix(metadata.suffix)
    sequence_type, name = DATABASES[base]

    rows.append(
        {
            "id": f"{taxon}-{owner_versions[-1]}-{sequence_type}",
            "owner": f"{taxon}-{owner_versions[-1]}",
            "ownerType": (
                "assembly" if len(owner_versions) == 1 else "annotation"
            ),
            "sequenceType": sequence_type,
            "moleculeType": metadata.parent.name,
            "name": name,
            "path": (metadata.parent.relative_to(ROOT) / base).as_posix(),
        }
    )

with OUTPUT.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: row["id"]))

print(f"wrote {len(rows)} rows to {OUTPUT}")
