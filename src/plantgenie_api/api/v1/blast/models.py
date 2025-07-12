from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class BlastBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


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
    job_id: str = Field(alias="jobId")
    program: Literal["blastn", "blastx", "blastp"] = Field(default="blastn")
    database_type: Literal["cds", "mrna", "prot", "genome"] = Field(
        alias="databaseType", default="genome"
    )
    file_size: int = Field(alias="fileSize")


# class BlastPollResponse(BlastBaseModel):
#     job_id: str = Field(alias="jobId")
#     status: Literal["PENDING", "SUCCESS", "FAILURE", "STARTED", "RETRY"]
#     result: Optional[str]
#     completed_at: Optional[str] = Field(alias="completedAt")

class BlastPollResponse(BlastBaseModel):
    job_id: str = Field(alias="jobId")
    status: Literal["PENDING", "SUCCESS", "FAILURE", "STARTED", "RETRY"]
    # result: Optional[str]
    completed_at: Optional[str] = Field(alias="completedAt")
