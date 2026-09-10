from typing import Annotated, Literal

from pydantic import Field

from plantgenie_api.models import PlantGenieModel

PROGRAMS = {
    ("nucl", "nucl"): ["blastn", "tblastx"],
    ("nucl", "prot"): ["blastx"],
    ("prot", "nucl"): ["tblastn"],
    ("prot", "prot"): ["blastp"],
}


class BlastParameters(PlantGenieModel):
    evalue: float = Field(default=1e-4, gt=0)
    max_target_seqs: int = Field(default=50, ge=1, le=1000)
    word_size: int | None = Field(default=None, ge=2)
    gapopen: int | None = Field(default=None, ge=0)
    gapextend: int | None = Field(default=None, ge=0)
    qcov_hsp_perc: float | None = Field(default=None, ge=0, le=100)


class BlastnParameters(BlastParameters):
    task: Literal[
        "megablast", "dc-megablast", "blastn", "blastn-short"
    ] = "megablast"
    penalty: int | None = Field(default=None, lt=0)
    reward: int | None = Field(default=None, gt=0)
    strand: Literal["both", "plus", "minus"] | None = None
    dust: Literal["yes", "no"] | None = None


class ProteinParameters(BlastParameters):
    matrix: (
        Literal["BLOSUM45", "BLOSUM62", "BLOSUM80", "PAM30", "PAM70"] | None
    ) = None
    seg: Literal["yes", "no"] | None = None
    comp_based_stats: int | None = Field(default=None, ge=0, le=3)


class TranslatedParameters(ProteinParameters):
    query_gencode: int | None = Field(default=None, ge=1, le=33)
    db_gencode: int | None = Field(default=None, ge=1, le=33)


class BlastRequest(PlantGenieModel):
    database_id: str
    query: str


class BlastnRequest(BlastRequest):
    program: Literal["blastn"]
    parameters: BlastnParameters = BlastnParameters()


class BlastpRequest(BlastRequest):
    program: Literal["blastp"]
    parameters: ProteinParameters = ProteinParameters()


class BlastxRequest(BlastRequest):
    program: Literal["blastx"]
    parameters: TranslatedParameters = TranslatedParameters()


class TblastnRequest(BlastRequest):
    program: Literal["tblastn"]
    parameters: TranslatedParameters = TranslatedParameters()


class TblastxRequest(BlastRequest):
    program: Literal["tblastx"]
    parameters: TranslatedParameters = TranslatedParameters()


SubmitBlastRequest = Annotated[
    BlastnRequest
    | BlastpRequest
    | BlastxRequest
    | TblastnRequest
    | TblastxRequest,
    Field(discriminator="program"),
]


class BlastDatabase(PlantGenieModel):
    id: str
    name: str
    sequence_type: str
    molecule_type: str
    taxon_scientific_name: str


class BlastDatabasesResponse(PlantGenieModel):
    databases: list[BlastDatabase]


class SubmitBlastResponse(PlantGenieModel):
    job_id: str


class BlastPollResponse(PlantGenieModel):
    status: str


class BlastHit(PlantGenieModel):
    query_id: str
    subject_id: str
    percent_identity: float
    alignment_length: int
    mismatches: int
    gap_opens: int
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    evalue: float
    bit_score: float

    @classmethod
    def from_tsv(cls, text: str) -> list["BlastHit"]:
        return [
            cls(
                **dict(zip(cls.model_fields, line.split("\t"), strict=True))
            )
            for line in text.strip().splitlines()
        ]


class BlastResultsResponse(PlantGenieModel):
    results: list[BlastHit]
