import time

from common.domain.job_a.job_schemas import JobAPayload, JobAResult


class JobAService:
    def process(self, payload: JobAPayload) -> JobAResult:
        time.sleep(1)
        return JobAResult(
            message=f"Processed Job A: {payload.message}", status="success"
        )
