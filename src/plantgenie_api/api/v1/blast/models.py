from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BlastProgramName(StrEnum):
    blastn = "blastn"
    blastp = "blastp"
    blastx = "blastx"


class BlastDatabaseType(StrEnum):
    cds = "cds"
    mrna = "mrna"
    prot = "prot"
    genome = "genome"


class BlastBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel
    )


class BlastVersion(BlastBaseModel):
    program: str
    version: str


class AvailableDatabase(BlastBaseModel):
    species: str
    genome: str
    sequence_type: str
    program: str
    database_path: str


class BlastSubmitResponse(BlastBaseModel):
    job_id: str
    program: BlastProgramName = Field(default=BlastProgramName.blastn)
    database_type: BlastDatabaseType = Field(
        default=BlastDatabaseType.genome
    )
    file_size: int


class BlastPollResponse(BlastBaseModel):
    job_id: str
    status: Literal["PENDING", "SUCCESS", "FAILURE", "STARTED", "RETRY"]
    completed_at: Optional[str]
