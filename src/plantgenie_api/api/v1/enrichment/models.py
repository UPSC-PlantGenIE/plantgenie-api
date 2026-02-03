from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class EnrichmentBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel
    )


class EnrichmentSubmissionResponse(EnrichmentBaseModel):
    job_id: str


class EnrichmentPollResponse(EnrichmentBaseModel):
    job_id: str
    status: Literal["PENDING", "SUCCESS", "FAILURE", "STARTED", "RETRY"]
    completed_at: Optional[str]
