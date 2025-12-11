from typing import Literal, Optional
from pydantic import BaseModel, Field


class VerifyExistsArgs(BaseModel):
    query_path: str


class VerifyFastaArgs(BaseModel):
    query_path: str
    program: Literal["blastn", "blastx", "blastp"]


class ExecuteBlastArgs(BaseModel):
    query_path: str
    program_name: Literal["blastn", "blastx", "blastp"]
    database_path: str
    evalue: Optional[float] = Field(default=0.0001, gt=0.0)
    max_hits: Optional[int] = Field(default=10, gt=0)
