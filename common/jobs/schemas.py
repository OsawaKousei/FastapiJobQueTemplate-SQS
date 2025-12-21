from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, Enum):
    JOB_A = "job_a"
    JOB_B = "job_b"
    JOB_C = "job_c"


class JobRequest(BaseModel):
    job_type: JobType
    payload: dict = Field(..., description="Payload for the job")


class Job(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    payload: dict
    result: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[str] = None
