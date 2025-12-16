import time
from common.domain.job_c.job_schemas import JobCPayload, JobCResult

class JobCService:
    def process(self, payload: JobCPayload) -> JobCResult:
        time.sleep(3)
        return JobCResult(tag_count=len(payload.tags), tags=payload.tags, status="success")
