from pydantic import BaseModel
from common.domain.job_a.job_schemas import JobAPayload

class CreateJobARequest(BaseModel):
    payload: JobAPayload
