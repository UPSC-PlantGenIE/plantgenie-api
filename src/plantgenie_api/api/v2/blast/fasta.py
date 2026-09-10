import re

RESIDUES = re.compile(r"^[A-Za-z*-]+$")
NUCLEOTIDES = set("ACGTUN")


def parse(query: str) -> list[tuple[str, str]]:
    text = query.strip()

    if not text.startswith(">"):
        raise ValueError("Query must be FASTA, beginning with a '>' header")

    records: list[tuple[str, str]] = []
    header = ""
    residues: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith(">"):
            if header or residues:
                records.append((header, "".join(residues)))
            header, residues = stripped[1:].strip(), []
            continue

        if not stripped:
            continue

        if not RESIDUES.match(stripped):
            raise ValueError(
                f"Sequence '{header}' contains characters that are neither "
                "nucleotides nor amino acids"
            )

        residues.append(stripped.upper())

    records.append((header, "".join(residues)))

    for record_header, sequence in records:
        if not sequence:
            raise ValueError(f"Sequence '{record_header}' has no residues")

    return records


def molecule_type(records: list[tuple[str, str]]) -> str:
    letters = {letter for _, sequence in records for letter in sequence}
    return "nucl" if letters <= NUCLEOTIDES else "prot"
