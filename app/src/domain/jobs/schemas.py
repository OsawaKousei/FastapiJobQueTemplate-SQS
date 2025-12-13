from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class JobRequest(BaseModel):
    payload: str = Field(..., description="Payload for the job")

class Job(BaseModel):
    job_id: str
    status: JobStatus
    payload: str
    result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[str] = None
