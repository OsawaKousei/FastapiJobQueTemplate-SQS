from pydantic import BaseModel
from common.domain.job_c.job_schemas import JobCPayload

class CreateJobCRequest(BaseModel):
    payload: JobCPayload
