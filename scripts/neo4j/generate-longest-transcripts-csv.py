"""Generate longest-transcripts.csv for longest-transcript-load.cypher.

Sequence fastas are keyed by transcript id while Gene nodes carry the
bare gene id, so the sequence endpoint needs the transcript id stored
on the gene.

Annotation ids do not compose uniformly from the directory tree, so
rows are keyed by the path that Annotation.path already stores.

One block per annotation, because the transcript id ends differently in
each one:

    betpe/v1/v1.2      Bpev01.c0000.g0001.m0001
    picab/v2/v2.0      PA_cUP0115_G000001.mRNA.1
    pinsy/v1/v1.0      PS_chr01_G000001.mRNA.2
    potra/T89-2026/h1  T89h1c1g00010.1
    potra/T89-2026/h2  T89h2c1g00010.1
    potra/v2/v2.2      Potra2n765s36715.1
    pruav/v2/v2.0      FUN_000003-T1

arath/tair10/araport11 and arath/tair10/tair10 have no sequence fastas,
so they have no block here and their genes get no transcript id.
"""

import csv
from pathlib import Path

ROOT = Path("/opt/data/plantgenie-knowledge")
OUTPUT = Path("/opt/neo4j/import/longest-transcripts.csv")
INDEX_NAME = "transcript-sequences.fa.gz.fai"
FIELDNAMES = ["path", "geneId", "longestTranscriptId"]

rows = []


path = "betpe/v1/v1.2"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit(".", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


path = "picab/v2/v2.0"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit(".mRNA.", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


path = "pinsy/v1/v1.0"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit(".mRNA.", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


path = "potra/T89-2026/h1"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit(".", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


path = "potra/T89-2026/h2"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit(".", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


path = "potra/v2/v2.2"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit(".", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


path = "pruav/v2/v2.0"
longest_by_gene = {}

for line in (ROOT / path / INDEX_NAME).read_text().splitlines():
    transcript_id, length = line.split("\t")[:2]
    gene_id = transcript_id.rsplit("-T", 1)[0]
    current = longest_by_gene.get(gene_id)

    if current is None or int(length) > current[1]:
        longest_by_gene[gene_id] = (transcript_id, int(length))

rows += [
    {
        "path": path,
        "geneId": gene_id,
        "longestTranscriptId": transcript_id,
    }
    for gene_id, (transcript_id, _) in longest_by_gene.items()
]


with OUTPUT.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"wrote {len(rows)} rows to {OUTPUT}")
