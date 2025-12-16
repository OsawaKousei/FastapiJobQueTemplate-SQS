from typing import Any, Dict
from common.jobs.schemas import Job, JobType
from common.domain.job_a.job_schemas import JobAPayload
from common.domain.job_b.job_schemas import JobBPayload
from common.domain.job_c.job_schemas import JobCPayload
from src.domain.job_a.service import JobAService
from src.domain.job_b.service import JobBService
from src.domain.job_c.service import JobCService

class JobDispatcher:
    def __init__(self):
        self.service_a = JobAService()
        self.service_b = JobBService()
        self.service_c = JobCService()

    def __call__(self, job: Job) -> Dict[str, Any]:
        match job.job_type:
            case JobType.JOB_A:
                payload = JobAPayload(**job.payload)
                return self.service_a.process(payload)
            case JobType.JOB_B:
                payload = JobBPayload(**job.payload)
                return self.service_b.process(payload)
            case JobType.JOB_C:
                payload = JobCPayload(**job.payload)
                return self.service_c.process(payload)
            case _:
                raise ValueError(f"Unknown job type: {job.job_type}")
