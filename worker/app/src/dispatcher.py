from typing import Any, Dict

from common.domain.job_a.job_schemas import JobAPayload
from common.domain.job_b.job_schemas import JobBPayload
from common.domain.job_c.job_schemas import JobCPayload
from common.jobs.schemas import Job, JobType
from src.domain.job_a.service import JobAService
from src.domain.job_b.service import JobBService
from src.domain.job_c.service import JobCService


class JobDispatcher:
    def __init__(self) -> None:
        self.service_a = JobAService()
        self.service_b = JobBService()
        self.service_c = JobCService()

    def __call__(self, job: Job) -> Dict[str, Any]:
        match job.job_type:
            case JobType.JOB_A:
                payload = JobAPayload(**job.payload)
                result = self.service_a.process(payload)
                return result.model_dump()
            case JobType.JOB_B:
                payload = JobBPayload(**job.payload)
                result = self.service_b.process(payload)
                return result.model_dump()
            case JobType.JOB_C:
                payload = JobCPayload(**job.payload)
                result = self.service_c.process(payload)
                return result.model_dump()
            case _:
                raise ValueError(f"Unknown job type: {job.job_type}")
