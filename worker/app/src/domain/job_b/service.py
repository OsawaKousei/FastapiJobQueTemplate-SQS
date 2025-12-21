import time

from common.domain.job_b.job_schemas import JobBPayload, JobBResult


class JobBService:
    def process(self, payload: JobBPayload) -> JobBResult:
        time.sleep(2)
        return JobBResult(count_squared=payload.count * payload.count, status="success")
