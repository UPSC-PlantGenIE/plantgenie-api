from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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
    program: Literal["blastn", "blastx", "blastp"] = Field(
        default="blastn"
    )
    database_type: Literal["cds", "mrna", "prot", "genome"] = Field(
        default="genome"
    )
    file_size: int


class BlastPollResponse(BlastBaseModel):
    job_id: str
    status: Literal["PENDING", "SUCCESS", "FAILURE", "STARTED", "RETRY"]
    # result: Optional[str]
    completed_at: Optional[str]
