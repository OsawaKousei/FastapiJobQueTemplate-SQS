from pydantic import BaseModel
from common.domain.job_b.job_schemas import JobBPayload

class CreateJobBRequest(BaseModel):
    payload: JobBPayload
