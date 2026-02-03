from typing import Optional
from pydantic import BaseModel, Field

from task_queue.blast import BlastProgram

class VerifyExistsArgs(BaseModel):
    query_path: str


class VerifyFastaArgs(BaseModel):
    query_path: str
    program: BlastProgram


class ExecuteBlastArgs(BaseModel):
    query_path: str
    program_name: BlastProgram
    database_path: str
    evalue: Optional[float] = Field(default=0.0001, gt=0.0)
    max_hits: Optional[int] = Field(default=10, gt=0)


class ExecuteBlastPipelineArgs(BaseModel):
    job_id: str
    blast_program: BlastProgram
    query_path: str
    database_path: str
    evalue: Optional[float] = Field(default=0.0001, gt=0.0)
    max_hits: Optional[int] = Field(default=10, gt=0)
